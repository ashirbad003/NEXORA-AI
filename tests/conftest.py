import os
import pytest
from backend.app.core.config import settings

# Enforce test database URL in environment
# If TEST_DATABASE_URL is set in backend/.env or environment, use that.
# Fall back to rewriting the database name in DATABASE_URL if it points to nexora_dev.
effective_test_url = os.environ.get("TEST_DATABASE_URL") or getattr(settings, "TEST_DATABASE_URL", "")

if not effective_test_url:
    base_url = settings.DATABASE_URL
    if "nexora_dev" in base_url:
        effective_test_url = base_url.replace("nexora_dev", "nexora_test")
    else:
        effective_test_url = base_url

# Override settings and environment variables
os.environ["DATABASE_URL"] = effective_test_url
settings.DATABASE_URL = effective_test_url

# Recreate the underlying SQLAlchemy engine and AsyncSessionLocal bound to test database
try:
    from backend.app.db.session import create_async_engine, get_engine_args
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    import backend.app.db.session as session_module

    new_engine = create_async_engine(effective_test_url, **get_engine_args())
    session_module.engine = new_engine
    session_module.AsyncSessionLocal = async_sessionmaker(
        bind=new_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
except Exception as e:
    raise RuntimeError(f"Failed to bind SQLAlchemy engine to test database: {e}")

@pytest.fixture(scope="session", autouse=True)
def guard_test_database_isolation():
    """
    Enforce strict test isolation (fail-closed protection):
    Verify that tests NEVER target or mutate the development database (nexora_dev).
    Checks both settings.DATABASE_URL and the live SQLAlchemy engine.url.
    """
    # 1. Check settings URL
    assert "nexora_dev" not in settings.DATABASE_URL, (
        f"CRITICAL TEST ISOLATION FAILURE: settings.DATABASE_URL targets development database"
    )
    assert "nexora_test" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL, (
        f"CRITICAL TEST ISOLATION FAILURE: settings.DATABASE_URL must target nexora_test or sqlite"
    )

    # 2. Check live SQLAlchemy engine URL
    import backend.app.db.session as session_module
    actual_engine_url = str(session_module.engine.url)
    assert "nexora_dev" not in actual_engine_url, (
        f"CRITICAL TEST ISOLATION FAILURE: Live engine is bound to development database"
    )
    assert "nexora_test" in actual_engine_url or "sqlite" in actual_engine_url, (
        f"CRITICAL TEST ISOLATION FAILURE: Live engine must target nexora_test or sqlite"
    )

    yield
