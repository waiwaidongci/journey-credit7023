import csv,io
from fastapi import HTTPException
from ..models import BudgetScenario,AttributionRun
from ..utils.serialize import record
from .audit_service import log
from .budget_algorithm import optimize_budget
from .run_service import queue

def list_scenarios(db):return [record(s) for s in db.query(BudgetScenario).order_by(BudgetScenario.id.desc())]
def get_scenario(db,sid):
    row=db.get(BudgetScenario,sid)
    if not row:raise HTTPException(404,"情景不存在")
    return row

def create_scenario(db,data,user):
    run=db.get(AttributionRun,data.run_id)
    if not run or run.status!="completed":raise HTTPException(409,"必须选已完成归因研究")
    try:optimize_budget(run.result['credits'],data.budget,data.capacity_overrides)
    except ValueError as e:raise HTTPException(422,str(e))
    row=BudgetScenario(**data.model_dump(),owner=user.name)
    db.add(row);db.flush();log(db,user.email,"scenario.enqueue",row.id);db.commit()
    try:queue.rpush("journey:jobs","scenario:"+str(row.id))
    except Exception:
        row.status="failed";row.error="队列不可用，请重试";db.commit();raise HTTPException(503,row.error)
    return record(row)
def review_scenario(db,sid,data,user):
    row=get_scenario(db,sid)
    if row.status!="completed":raise HTTPException(409,"只能复核已完成情景")
    if row.review_status!="submitted":raise HTTPException(409,"已复核情景不能重复审批")
    row.review_status=data.status;row.reviewer=user.name;row.review_note=data.review_note
    log(db,user.email,"scenario."+data.status,row.id);db.commit();return record(row)
def export_scenario(db,sid):
    row=get_scenario(db,sid)
    if row.status!="completed" or row.review_status!="approved":raise HTTPException(403,"只有获批完成情景可以导出")
    out=io.StringIO();w=csv.writer(out);w.writerow(['channel','allocation','unit_cost','capacity','spend','association_score','proxy_contribution','attribution_share','input_hash'])
    for x in row.result['allocations']:w.writerow([x[k] for k in ['code','allocation','unit_cost','capacity','spend','association_score','proxy_contribution','share']]+[row.result['input_hash']])
    return out.getvalue()
