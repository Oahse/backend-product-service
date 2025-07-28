from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, DateTime, Boolean,DECIMAL
from core.database import Base, CHAR_LENGTH
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_percent: Mapped[float] = mapped_column(DECIMAL(5, 2), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "discount_percent": float(self.discount_percent),
            "active": self.active,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }
