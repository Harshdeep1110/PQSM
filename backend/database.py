"""
Module: backend.database
Purpose: SQLite database setup using SQLAlchemy ORM.
         Defines tables for users and encrypted messages.
Created by: TASK-05

Storage: SQLite (zero-config, file-based, no server process needed)
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    LargeBinary,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------
# Store the database file in the project root
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "pqc_messenger.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with check_same_thread=False for FastAPI async compatibility
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------
class UserRecord(Base):
    """
    Stores registered users and their PUBLIC keys.
    Private keys are returned to the user at registration and never stored.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    # Password stored as PBKDF2-SHA256 hash + salt (never plaintext)
    password_hash = Column(String(128), nullable=False)
    password_salt = Column(String(64), nullable=False)
    # Public keys stored as raw bytes (binary blobs)
    public_key_kyber = Column(LargeBinary, nullable=False)
    public_key_dilithium = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MessageRecord(Base):
    """
    Stores encrypted messages between users.
    The server NEVER stores plaintext — only ciphertext + crypto metadata.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String(64), nullable=False, index=True)
    receiver = Column(String(64), nullable=False, index=True)
    # Encrypted message data (all hex-encoded strings)
    ciphertext = Column(Text, nullable=False)
    nonce = Column(String(64), nullable=False)
    tag = Column(String(64), nullable=False)
    signature = Column(Text, nullable=False)
    # KEM ciphertext needed for the receiver to decapsulate the shared secret
    kem_ciphertext = Column(Text, nullable=False, default="")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------
def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency — yields a database session.
    Ensures the session is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"Database created at: {DB_PATH}")
    print("Tables: users, messages")
    print("Done!")
