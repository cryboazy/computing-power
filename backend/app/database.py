import re
from urllib.parse import quote_plus

from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


def _parse_server_version(version_str):
    match = re.search(r'(\d+)\.(\d+)', version_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), 0)
    return (7, 0, 0)


_original_get_server_version_info = PGDialect_psycopg2._get_server_version_info


def _patched_get_server_version_info(self, connection):
    try:
        return _original_get_server_version_info(self, connection)
    except AssertionError:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW server_version")
                version_str = cursor.fetchone()[0]
                return _parse_server_version(version_str)
        except Exception:
            return (7, 0, 0)


PGDialect_psycopg2._get_server_version_info = _patched_get_server_version_info

encoded_password = quote_plus(settings.DB_PASSWORD)
DATABASE_URL = f"postgresql://{settings.DB_USER}:{encoded_password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    isolation_level="AUTOCOMMIT",
    connect_args={
        "sslmode": "prefer"
    }
)


@event.listens_for(engine, "connect")
def set_encoding(dbapi_connection, connection_record):
    dbapi_connection.set_client_encoding('UTF8')


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
