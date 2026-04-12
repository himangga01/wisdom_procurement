from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    # Import models so SQLAlchemy can discover metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
