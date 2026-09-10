from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("usr_id",Integer, primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column("usr_name",String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column("usr_email",String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column("usr_image_path",
        String(200),
        nullable=True,
        default=None,
    )

    posts: Mapped[list[Post]] = relationship(back_populates="author")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column("pst_id",Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column("pst_title",String(100), nullable=False)
    content: Mapped[str] = mapped_column("pst_content",Text, nullable=False)
    user_id: Mapped[int] = mapped_column("pst_user_id",
        ForeignKey("users.usr_id"),
        nullable=False,
        index=True,
    )
    date_posted: Mapped[datetime] = mapped_column("pst_date_posted",
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    author: Mapped[User] = relationship(back_populates="posts")