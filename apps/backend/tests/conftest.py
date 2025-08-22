import pytest
import asyncio
import subprocess
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db

# Use synchronous PostgreSQL for tests
TEST_DATABASE_URL = "postgresql://observastack:observastack@localhost:5432/observastack"

# Create synchronous engine and session
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override with synchronous database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup database using Alembic migrations."""
    # Change to backend directory for alembic commands
    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    original_cwd = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        
        # Set environment variable for database URL
        env = os.environ.copy()
        env["DATABASE_URL"] = TEST_DATABASE_URL
        
        # Run Alembic upgrade to create tables
        result = subprocess.run(
            ["/home/lohi/src/kiro/observastack/apps/backend/venv/bin/alembic", "upgrade", "head"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Alembic upgrade failed: {result.stderr}")
            # Fallback to manual table creation if Alembic fails
            from app.db.session import Base
            Base.metadata.create_all(bind=engine)
        
        yield
        
        # Clean up: downgrade all migrations
        subprocess.run(
            ["/home/lohi/src/kiro/observastack/apps/backend/venv/bin/alembic", "downgrade", "base"],
            env=env,
            capture_output=True,
            text=True
        )
        
    finally:
        os.chdir(original_cwd)

@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test."""
    db = TestingSessionLocal()
    try:
        # Clean in reverse order due to foreign key constraints
        db.execute(text("DELETE FROM users"))
        db.execute(text("DELETE FROM tenants"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)