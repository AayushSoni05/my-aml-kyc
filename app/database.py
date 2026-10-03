"""
Sets up the database connection (the "engine") and gives the rest of the
app a way to open a session to talk to it.
"""
from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db():
    """Creates all tables that don't exist yet, based on our models."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Opens a database session, used by scripts and later by API endpoints."""
    with Session(engine) as session:
        yield session