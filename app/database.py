from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def build_engine_config() -> tuple[str, dict[str, Any]]:
    if settings.turso_database_url:
        try:
            import sqlalchemy_libsql  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "sqlalchemy-libsql nao esta instalado. Para usar Turso localmente, rode via Docker/WSL/Linux "
                "ou instale os build tools necessarios no Windows."
            ) from exc

        if not settings.turso_auth_token:
            raise RuntimeError("TURSO_AUTH_TOKEN deve ser configurado quando TURSO_DATABASE_URL for usado.")

        database_url = settings.turso_database_url.strip()
        sqlalchemy_url = database_url if database_url.startswith("sqlite+libsql://") else f"sqlite+{database_url}"

        separator = "&" if "?" in sqlalchemy_url else "?"
        if "secure=" not in sqlalchemy_url:
            sqlalchemy_url = f"{sqlalchemy_url}{separator}secure=true"

        return sqlalchemy_url, {
            "pool_pre_ping": True,
            "connect_args": {"auth_token": settings.turso_auth_token},
        }

    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    return settings.database_url, {
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }


engine_url, engine_kwargs = build_engine_config()
engine = create_engine(engine_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
