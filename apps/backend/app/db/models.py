from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Tenant(Base):
    """Tenant model for multi-tenancy support."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to users
    users = relationship("User", back_populates="tenant")


class User(Base):
    """User model for local authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    username = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    roles = Column(JSON, nullable=True)  # JSON string for roles
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to tenant
    tenant = relationship("Tenant", back_populates="users")