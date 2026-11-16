from fastapi import HTTPException
from ..models import JourneyBatch,Journey
from ..utils.serialize import record
from .audit_service import log

def list_journeys(db,bid):
    if not db.get(JourneyBatch,bid):raise HTTPException(404,"路径批次不存在")
    return [record(j) for j in db.query(Journey).filter_by(batch_id=bid).order_by(Journey.code)]
def annotate_journey(db,jid,data,user):
    row=db.get(Journey,jid)
    if not row:raise HTTPException(404,"路径不存在")
    row.note=data.note;log(db,user.email,"journey.annotate",row.id);db.commit();return record(row)
