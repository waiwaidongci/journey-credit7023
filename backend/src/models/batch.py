from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class JourneyBatch(Base):
    __tablename__="journey_batches"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(unique=True)
    source:Mapped[str]
    description:Mapped[str]
