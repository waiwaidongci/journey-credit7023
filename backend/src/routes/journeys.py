from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import roles
from ..constants.roles import Role
from ..schemas.journey import JourneyAnnotation
from ..services.journey_service import annotate_journey
router=APIRouter(prefix="/journeys",tags=["journeys"])
@router.patch("/{jid}")
def annotate(jid:int,data:JourneyAnnotation,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return annotate_journey(db,jid,data,user)
