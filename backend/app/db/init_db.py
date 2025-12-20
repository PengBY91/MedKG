"""
Database initialization script
Run this to create all tables in the database
"""
from app.db.base import Base, engine, init_db
from app.db.models import (
    PolicyDocument, Rule, Terminology, DataAsset,
    WorkflowInstance, User, Tenant
)

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    init_db()
    print("✓ Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
