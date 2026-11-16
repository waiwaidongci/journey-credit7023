import math
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user,roles
from ..constants.roles import Role
from ..schemas.run import RunInput
from ..services.run_service import list_runs,get_run,create_run,transition_rows
from ..utils.serialize import record
router=APIRouter(prefix="/runs",tags=["runs"])
@router.get("")
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_runs(db)
@router.get("/{rid}")
def show(rid:int,db:Session=Depends(get_db),user=Depends(current_user)):return record(get_run(db,rid))
@router.get("/{rid}/transitions")
def transitions(rid:int,source:str|None=None,page:int=1,per_page:int=25,db:Session=Depends(get_db),user=Depends(current_user)):
    """转移明细按来源渠道分页；只返回请求页的来源行，不传输完整方阵。"""
    row=get_run(db,rid);rows=transition_rows(row.result)
    if rows is None:raise HTTPException(404,"该研究尚无转移明细")
    per_page=min(max(per_page,1),100);total_edges=sum(len(r['edges']) for r in rows)
    if source is not None:
        match=[r for r in rows if r['source']==source]
        if not match:raise HTTPException(404,"来源状态不存在")
        return {"run_id":rid,"page":1,"per_page":per_page,"pages":1,"total_sources":len(rows),"total_edges":total_edges,"rows":match}
    pages=max(1,math.ceil(len(rows)/per_page));page=min(max(page,1),pages)
    return {"run_id":rid,"page":page,"per_page":per_page,"pages":pages,"total_sources":len(rows),"total_edges":total_edges,"rows":rows[(page-1)*per_page:page*per_page]}
@router.post("",status_code=202)
def create(data:RunInput,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return create_run(db,data,user)
