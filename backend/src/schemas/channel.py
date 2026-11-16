from pydantic import BaseModel
class ChannelOutput(BaseModel):
    id:int
    code:str
    name:str
    unit_cost:float
    capacity:float
    description:str
