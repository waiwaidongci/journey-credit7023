from pydantic import BaseModel
class BatchOutput(BaseModel):
    id:int
    name:str
    source:str
    description:str
    journey_count:int
    conversions:int
