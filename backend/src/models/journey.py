from sqlalchemy import ForeignKey,JSON
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class Journey(Base):
    __tablename__="journeys"
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(unique=True)
    batch_id:Mapped[int]=mapped_column(ForeignKey("journey_batches.id"))
    path:Mapped[list]=mapped_column(JSON)
    converted:Mapped[bool]
    note:Mapped[str]
