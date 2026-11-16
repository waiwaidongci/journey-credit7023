from pydantic import BaseModel,Field
class JourneyOutput(BaseModel):
    id:int
    code:str
    batch_id:int
    path:list[str]
    converted:bool
    note:str
class JourneyAnnotation(BaseModel):
    note:str=Field(min_length=8,max_length=1500)
