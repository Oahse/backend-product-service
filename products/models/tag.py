from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String
from core.database import Base, CHAR_LENGTH
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, name={self.name!r})"

