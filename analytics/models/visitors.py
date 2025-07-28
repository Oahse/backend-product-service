from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Date, Integer, String,CheckConstraint
from core.database import Base,CHAR_LENGTH  # your declarative base


from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, Integer
from core.database import Base, CHAR_LENGTH

class UserLocationStats(Base):
    __tablename__ = "user_location_stats"

    country: Mapped[str] = mapped_column(String(CHAR_LENGTH), primary_key=True)
    state: Mapped[str] = mapped_column(String(CHAR_LENGTH), primary_key=True)
    date: Mapped[Date] = mapped_column(primary_key=True)
    users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "country": self.country,
            "state": self.state,
            "date": self.date.isoformat(),
            "users": self.users
        }

    def __repr__(self):
        return (
            f"<UserLocationStats(country='{self.country}', state='{self.state}', "
            f"date={self.date}, users={self.users})>"
        )

class VisitorEvents(Base):
    __tablename__ = "visitor_events"
    __table_args__ = (
        CheckConstraint('visitors >= 0', name='check_visitors_nonnegative'),
    )

    source: Mapped[str] = mapped_column(String(CHAR_LENGTH), primary_key=True)
    date: Mapped[Date] = mapped_column(Date, primary_key=True)
    visitors: Mapped[int] = mapped_column(Integer)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "date": str(self.date),
            "visitors": self.visitors
        }

    def __repr__(self) -> str:
        return (
            f"<VisitorEvents(source={self.source!r}, date={self.date}, "
            f"visitors={self.visitors})>"
        )
