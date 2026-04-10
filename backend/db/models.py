from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    history_records: Mapped[list["AnalysisHistoryRecord"]] = relationship(back_populates="user")
    session_snapshots: Mapped[list["SessionSnapshotRecord"]] = relationship(back_populates="user")


class AnalysisHistoryRecord(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    match_key: Mapped[str] = mapped_column(String(255), index=True)
    batting_team: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bowling_team: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    score: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    win_probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="history_records")


class SessionSnapshotRecord(Base):
    __tablename__ = "session_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    match_key: Mapped[str] = mapped_column(String(255), index=True)
    score: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    win_probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="session_snapshots")
