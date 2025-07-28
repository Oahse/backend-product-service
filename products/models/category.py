from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text
from core.database import Base, CHAR_LENGTH
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, index=False)  # Usually text fields are not indexed

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"