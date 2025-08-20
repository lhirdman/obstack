import pytest
from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal


@pytest.mark.asyncio
async def test_database_connection():
    """Test that the application can successfully connect to the PostgreSQL database."""
    async with engine.begin() as conn:
        # Test basic connection with a simple query
        result = await conn.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        
        assert row is not None
        assert row.test_value == 1


@pytest.mark.asyncio
async def test_database_session():
    """Test that we can create a database session and perform a simple query."""
    async with AsyncSessionLocal() as session:
        # Perform a simple query to test the connection
        result = await session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        
        assert row is not None
        assert row.test_value == 1


@pytest.mark.asyncio
async def test_database_session_transaction():
    """Test database session transaction handling."""
    async with AsyncSessionLocal() as session:
        # Test that we can perform queries within a transaction
        result = await session.execute(text("SELECT 'connection_test' as message"))
        row = result.fetchone()
        
        assert row is not None
        assert row.message == "connection_test"


@pytest.mark.asyncio
async def test_init_db_function():
    """Test the init_db function works correctly."""
    from app.db.session import init_db
    
    result = await init_db()
    assert result is True