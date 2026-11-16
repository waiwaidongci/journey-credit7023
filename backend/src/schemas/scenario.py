from typing import Literal
from pydantic import BaseModel,Field
class ScenarioInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    run_id:int
    budget:float=Field(gt=0,le=1e7,allow_inf_nan=False)
    capacity_overrides:dict[str,float]=Field(default_factory=dict)
class ReviewInput(BaseModel):
    status:Literal["approved","rejected"]
    review_note:str=Field(min_length=8,max_length=1500)
