"""
Configuration SQLAlchemy - Base, Engine, SessionLocal.
Lit DB_URL depuis l'environnement (.env ou variable).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Charger .env si présent
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration DB
DB_URL = os.getenv("DB_URL", "sqlite:///./data/app.db")

# Créer le répertoire data si SQLite
if DB_URL.startswith("sqlite"):
    db_path = Path(DB_URL.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Engine SQLAlchemy
engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {},
)

# SessionLocal pour les transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles ORM
Base = declarative_base()


def get_db():  # type: ignore[no-untyped-def]
    """
    Générateur de session DB pour dependency injection.
    Usage: with get_db() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

