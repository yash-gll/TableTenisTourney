import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class RatingConfig(UUIDMixin, Base):
    __tablename__ = "rating_config"

    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    starting_rating: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    rating_floor: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    group_k: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    qf1_k: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    qf2_k: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    qf3_k: Mapped[int] = mapped_column(Integer, default=28, nullable=False)
    final_k: Mapped[int] = mapped_column(Integer, default=32, nullable=False)
    champion_bonus: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    runner_up_bonus: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    third_place_bonus: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
