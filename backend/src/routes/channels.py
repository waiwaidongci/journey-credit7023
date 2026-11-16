from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user
from ..schemas.channel import ChannelOutput
from ..services.channel_service import list_channels
router=APIRouter(prefix="/channels",tags=["channels"])
@router.get("",response_model=list[ChannelOutput])
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_channels(db)
