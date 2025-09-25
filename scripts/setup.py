#!/usr/bin/env python3
"""
Setup script for the Financial Transaction Aggregator application.
This script initializes the database and creates necessary tables.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models import *  # Import all models


def create_database():
    """Create database tables"""
    print("Creating database tables...")
    
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")


def run_migrations():
    """Run Alembic migrations"""
    print("Running database migrations...")
    
    try:
        # Initialize Alembic if not already done
        subprocess.run(["alembic", "init", "alembic"], check=False, cwd=project_root)
        
        # Generate initial migration
        subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
            check=True,
            cwd=project_root
        )
        
        # Apply migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=project_root)
        
        print("Migrations completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, cwd=project_root)
        
        print("Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Setup environment file"""
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"Created {env_file}")
        print("Please update the .env file with your actual configuration values!")
    else:
        print(".env file already exists or .env.example not found")


def main():
    """Main setup function"""
    print("Setting up Financial Transaction Aggregator...")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: Not running in a virtual environment!")
        print("It's recommended to create and activate a virtual environment first.")
        print()
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed during dependency installation!")
        return 1
    
    # Create database tables (fallback if migrations fail)
    try:
        create_database()
    except Exception as e:
        print(f"Failed to create database tables: {e}")
        print("Make sure your database is running and connection details are correct in .env")
        return 1
    
    # Run migrations
    if not run_migrations():
        print("Migrations failed, but basic tables were created.")
    
    print()
    print("=" * 50)
    print("Setup completed!")
    print()
    print("Next steps:")
    print("1. Update your .env file with correct database and API credentials")
    print("2. Start the database: docker-compose up postgres redis -d")
    print("3. Run the application: uvicorn app.main:app --reload")
    print("4. Start Celery worker: celery -A app.tasks worker --loglevel=info")
    print("5. Visit http://localhost:8000/docs for API documentation")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())