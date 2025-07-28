from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Date, Integer, Float
from core.database import Base  # assuming Base is declarative base

class DailyKPIs(Base):
    __tablename__ = "daily_kpis"

    date: Mapped = mapped_column(Date, primary_key=True)
    total_orders: Mapped[int] = mapped_column(Integer)
    total_revenue: Mapped[float] = mapped_column(Float)
    total_customers: Mapped[int] = mapped_column(Integer)
    total_earnings: Mapped[float] = mapped_column(Float)

    def to_dict(self) -> dict:
        return {
            "date": str(self.date),
            "total_orders": self.total_orders,
            "total_revenue": self.total_revenue,
            "total_customers": self.total_customers,
            "total_earnings": self.total_earnings,
        }

    def __repr__(self) -> str:
        return (
            f"<DailyKPIs(date={self.date}, orders={self.total_orders}, "
            f"revenue={self.total_revenue}, customers={self.total_customers}, "
            f"earnings={self.total_earnings})>"
        )


class OrderEvents(Base):
    __tablename__ = "order_events"

    date: Mapped = mapped_column(Date, primary_key=True)
    total_orders: Mapped[int] = mapped_column(Integer)
    total_revenue: Mapped[float] = mapped_column(Float)
    total_earnings: Mapped[float] = mapped_column(Float)

    def to_dict(self) -> dict:
        return {
            "date": str(self.date),
            "total_orders": self.total_orders,
            "total_revenue": self.total_revenue,
            "total_earnings": self.total_earnings,
        }

    def __repr__(self) -> str:
        return (
            f"<OrderEvents(date={self.date}, orders={self.total_orders}, "
            f"revenue={self.total_revenue}, earnings={self.total_earnings})>"
        )
