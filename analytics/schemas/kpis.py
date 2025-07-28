from pydantic import BaseModel, conint, confloat
from datetime import date

class DailyKPIsSchema(BaseModel):
    date: date
    total_orders: conint(ge=0)        # non-negative int
    total_revenue: confloat(ge=0.0)   # non-negative float
    total_customers: conint(ge=0)     # non-negative int
    total_earnings: confloat(ge=0.0)  # non-negative float

    class Config:
        from_attributes = True


class OrderEventsSchema(BaseModel):
    date: date
    total_orders: conint(ge=0)
    total_revenue: confloat(ge=0.0)
    total_earnings: confloat(ge=0.0)

    class Config:
        from_attributes = True
