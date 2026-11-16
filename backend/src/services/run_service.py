from redis import Redis
from fastapi import HTTPException
from ..config.settings import REDIS_URL
from ..models import AttributionRun,JourneyBatch
from ..utils.serialize import record
from .audit_service import log
queue=Redis.from_url(REDIS_URL,decode_responses=True)
def list_runs(db):return [record(r) for r in db.query(AttributionRun).order_by(AttributionRun.id.desc())]
def get_run(db,rid):
    row=db.get(AttributionRun,rid)
    if not row:raise HTTPException(404,"归因研究不存在")
    return row

def create_run(db,data,user):
    if not db.get(JourneyBatch,data.batch_id):raise HTTPException(404,"路径批次不存在")
    row=AttributionRun(**data.model_dump(),owner=user.name)
    db.add(row);db.flush();log(db,user.email,"attribution.enqueue",row.id);db.commit()
    try:queue.rpush("journey:jobs","run:"+str(row.id))
    except Exception:
        row.status="failed";row.error="队列不可用，请重试";db.commit();raise HTTPException(503,row.error)
    return record(row)
