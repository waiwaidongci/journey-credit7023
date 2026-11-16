from redis import Redis
from fastapi import HTTPException
from ..config.settings import REDIS_URL
from ..models import AttributionRun,JourneyBatch
from ..utils.serialize import record
from .audit_service import log
queue=Redis.from_url(REDIS_URL,decode_responses=True)
HEAVY_RESULT_FIELDS={"transition_matrix","transition_counts","transition_edges"}
def slim_result(result):return {k:v for k,v in (result or {}).items() if k not in HEAVY_RESULT_FIELDS}
def list_runs(db):return [dict(record(r),result=slim_result(r.result)) for r in db.query(AttributionRun).order_by(AttributionRun.id.desc())]
def get_run(db,rid):
    row=db.get(AttributionRun,rid)
    if not row:raise HTTPException(404,"归因研究不存在")
    return row

def transition_rows(result):
    """按来源状态分组的转移明细；新格式读稀疏边，旧格式从内嵌方阵展开，旧研究保持可查。"""
    result=result or {};states=result.get('states') or []
    if result.get('transition_edges') is not None:
        grouped={s:[] for s in states}
        for e in result['transition_edges']:grouped[e['source']].append({"target":e['target'],"probability":e['probability'],"count":e['count']})
        return [{"source":s,"edges":grouped[s]} for s in states]
    if result.get('transition_matrix') is not None:
        matrix=result['transition_matrix'];counts=result.get('transition_counts') or [[0.]*len(states) for _ in states]
        return [{"source":s,"edges":[{"target":states[j],"probability":matrix[i][j],"count":counts[i][j]} for j in range(len(states)) if matrix[i][j]>0]} for i,s in enumerate(states)]
    return None

def create_run(db,data,user):
    if not db.get(JourneyBatch,data.batch_id):raise HTTPException(404,"路径批次不存在")
    row=AttributionRun(**data.model_dump(),owner=user.name)
    db.add(row);db.flush();log(db,user.email,"attribution.enqueue",row.id);db.commit()
    try:queue.rpush("journey:jobs","run:"+str(row.id))
    except Exception:
        row.status="failed";row.error="队列不可用，请重试";db.commit();raise HTTPException(503,row.error)
    return record(row)
