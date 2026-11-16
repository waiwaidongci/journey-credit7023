from sqlalchemy import ForeignKey,JSON
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class BudgetScenario(Base):
    __tablename__="budget_scenarios"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]
    run_id:Mapped[int]=mapped_column(ForeignKey("attribution_runs.id"))
    budget:Mapped[float]
    capacity_overrides:Mapped[dict]=mapped_column(JSON,default=dict)
    status:Mapped[str]=mapped_column(default="queued")
    review_status:Mapped[str]=mapped_column(default="submitted")
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(default="")
    owner:Mapped[str]
    reviewer:Mapped[str]=mapped_column(default="")
    review_note:Mapped[str]=mapped_column(default="")
    created_at:Mapped[str]=mapped_column(default=now)
