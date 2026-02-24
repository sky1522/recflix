"""
Shared pytest fixtures.

Uses SQLite in-memory for fast, isolated tests.
PostgreSQL-specific features are skipped.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine, event

# Map PostgreSQL JSONB → JSON for SQLite compatibility
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_db
from app.database import Base
from app.main import app

for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, JSONB):
            column.type = JSON()

# SQLite in-memory engine (shared across a single test)
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL and foreign keys for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# Disable rate limiting in tests
from app.core.rate_limit import limiter  # noqa: E402

limiter.enabled = False

# Mock Redis as unavailable (no Redis in test environment)
import app.api.v1.auth as _auth_mod  # noqa: E402
import app.api.v1.movies as _movies_mod  # noqa: E402
import app.api.v1.users as _users_mod  # noqa: E402
import app.services.llm as _llm_mod  # noqa: E402
import app.services.weather as _weather_mod  # noqa: E402


async def _no_redis() -> None:
    return None


for _mod in (_llm_mod, _weather_mod, _auth_mod, _movies_mod, _users_mod):
    _mod.get_redis_client = _no_redis  # type: ignore[assignment]


@pytest.fixture()
def client():
    """FastAPI TestClient bound to the SQLite test DB."""
    return TestClient(app)


@pytest.fixture()
def db():
    """Raw DB session for seeding test data."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
