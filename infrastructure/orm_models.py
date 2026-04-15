# -*- coding: utf-8 -*-
"""SQLAlchemy ORM — mirror of legacy DDL in ``models.connection.init_db`` (P3)."""
from __future__ import annotations

from sqlalchemy import Float, Integer, Text, UniqueConstraint
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
            name="ux_data_entry_variant",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uploader_name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    template_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicator_name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class AggregatedSummary(Base):
    __tablename__ = "aggregated_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
