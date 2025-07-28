from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String
from core.database import Base, CHAR_LENGTH


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, name={self.name!r})"

