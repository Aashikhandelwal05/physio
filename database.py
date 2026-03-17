import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Use environment variable for database URL in production, default to local SQLite for development
# On Railway, this will likely be sqlite:////data/physio.db
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./physio.db")

# Create engine. If it's SQLite, check_same_thread=False is needed.
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models (modern SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
