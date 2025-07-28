from pydantic import BaseModel, constr, conint
from datetime import date
from typing import Optional
from core.database import CHAR_LENGTH
class VisitorEventsSchema(BaseModel):
    source: constr(max_length=CHAR_LENGTH)
    date: date
    visitors: conint(ge=0)  # visitors must be >= 0

    class Config:
        from_attributes = True

class UserLocationStatsBase(BaseModel):
    country: str
    state: str
    date: date
    users: int

    class Config:
        from_attributes = True

class UserLocationStatsCreate(BaseModel):
    country: str
    state: str
    date: date
    users: Optional[int] = 0


class UserLocationStatsResponse(UserLocationStatsBase):
    pass