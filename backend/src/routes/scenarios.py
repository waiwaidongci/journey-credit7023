from fastapi import APIRouter,Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user,roles
from ..constants.roles import Role
from ..schemas.scenario import ScenarioInput,ReviewInput
from ..services.scenario_service import list_scenarios,get_scenario,create_scenario,review_scenario,export_scenario
from ..utils.serialize import record
router=APIRouter(prefix="/scenarios",tags=["scenarios"])
@router.get("")
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_scenarios(db)
@router.get("/{sid}")
def show(sid:int,db:Session=Depends(get_db),user=Depends(current_user)):return record(get_scenario(db,sid))
@router.post("",status_code=202)
def create(data:ScenarioInput,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return create_scenario(db,data,user)
@router.patch("/{sid}/review")
def review(sid:int,data:ReviewInput,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN))):return review_scenario(db,sid,data,user)
@router.get("/{sid}/export")
def export(sid:int,db:Session=Depends(get_db),user=Depends(current_user)):return Response(content='﻿'+export_scenario(db,sid),media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="journey-scenario-{sid}.csv"'})
