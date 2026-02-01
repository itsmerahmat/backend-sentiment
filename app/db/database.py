from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings


# Create database engine for PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session
