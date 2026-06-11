from sqlmodel import SQLModel, create_engine, Session
from .config import settings

engine = create_engine(settings.database_url, echo=settings.environment == "development")


def get_session():
    with Session(engine) as session:
        yield session
