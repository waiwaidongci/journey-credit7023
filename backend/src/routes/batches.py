from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user
from ..schemas.batch import BatchOutput
from ..schemas.journey import JourneyOutput
from ..services.batch_service import list_batches
from ..services.journey_service import list_journeys
router=APIRouter(prefix="/batches",tags=["batches"])
@router.get("",response_model=list[BatchOutput])
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_batches(db)
@router.get("/{bid}/journeys",response_model=list[JourneyOutput])
def journeys(bid:int,db:Session=Depends(get_db),user=Depends(current_user)):return list_journeys(db,bid)
