# -*- coding: utf-8 -*-
"""SQLAlchemy ORM — mirror of legacy DDL in ``models.connection.init_db`` (P3)."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for application tables."""


class DataEntry(Base):
    __tablename__ = "data_entries"
    __table_args__ = (
        UniqueConstraint(
            "uploader_name",
            "version",
            "indicator_name",
            "year",
            "month",
            "quarter",
            "dataset_code",
            name="ux_data_entry_variant",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uploader_name: Mapped[str] = mapped_column(String(191), nullable=False)
    version: Mapped[str] = mapped_column(String(191), nullable=False)
    template_type: Mapped[str | None] = mapped_column(String(191), nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    indicator_name: Mapped[str] = mapped_column(String(191), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")


class UploadRun(Base):
    """Audit ringkas per unggahan (Fase 4)."""

    __tablename__ = "upload_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    uploader_name: Mapped[str] = mapped_column(String(191), nullable=False)
    version: Mapped[str] = mapped_column(String(191), nullable=False)
    dataset_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
