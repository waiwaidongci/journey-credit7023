from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class Channel(Base):
    __tablename__="channels"
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(unique=True)
    name:Mapped[str]
    unit_cost:Mapped[float]
    capacity:Mapped[float]
    description:Mapped[str]
