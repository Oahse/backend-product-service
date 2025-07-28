from pydantic import BaseModel, Field

class TagBase(BaseModel):
    name: str = Field(..., max_length=100)

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: str

    class Config:
        from_attributes = True

