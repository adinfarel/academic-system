"""
database.py — PostgreSQL connection and session management

Using SQLAlchemy as an ORM (Object Relational Mapper).
ORM = you write a Python class, SQLAlchemy handles the SQL queries.
"""

from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError
from backend.config import get_settings

settings = get_settings()

# ENGINE
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base Model
class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    Every model (Student, Lecturer, etc.) must inherit from this class.
    so SQLAlchemy knows they are database tables.
    """
    pass

# Depedency Injection
def get_db():
    """
    Generator function for FastAPI dependency injection.

    How it works:
    1. Open a new session for each incoming request.
    2. Inject the session into the route handler.
    3. After the request completes (or an error occurs), the session MUST be closed.

    How to use it in the router:
    from backend.database import get_db
    from sqlalchemy.org import Session
    from fastapi import Depends

    @router.get("/example")
    def example(db: Session = Depends(get_db)):
    ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check 
def check_db_connection() -> bool:
    """
    Checks if the connection to PostgreSQL was successful.
    Called at startup in main.py for early detection if the database is down.

    Returns:
    bool: True if the connection was successful, False if it failed
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT_1"))
        return True
    except OperationalError as e:
        logger.error(f"[DB ERROR] Connection failed to database: {e}")
        return False
            