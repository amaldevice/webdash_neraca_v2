# -*- coding: utf-8 -*-
import os

from config import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, "data.db")


def init_db() -> None:
    """Create application tables on the bound SQLAlchemy engine (idempotent ``create_all``)."""
    from sqlalchemy.exc import SQLAlchemyError

    from infrastructure.db import get_engine, is_engine_initialized
    from infrastructure.orm_models import Base

    if not is_engine_initialized():
        raise RuntimeError(
            "init_db requires an initialized SQLAlchemy engine; call init_engine(database_url()) first."
        )
    eng = get_engine()
    if eng is None:
        raise RuntimeError("init_db: engine is missing.")
    try:
        Base.metadata.create_all(bind=eng)
    except SQLAlchemyError:
        raise
