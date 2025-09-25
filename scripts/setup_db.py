#!/usr/bin/env python3
"""
Database setup script for Financial Data Aggregator
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.config import settings

def create_database():
    """Create the database if it doesn't exist"""
    # Extract database name from URL
    db_url = settings.database_url
    if db_url.startswith('postgresql://'):
        # Parse the URL to get database name
        parts = db_url.split('/')
        db_name = parts[-1]
        base_url = '/'.join(parts[:-1])
        
        # Connect to postgres database to create our database
        postgres_url = base_url + '/postgres'
        
        try:
            engine = create_engine(postgres_url)
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
                if not result.fetchone():
                    # Create database
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    print(f"Database '{db_name}' created successfully")
                else:
                    print(f"Database '{db_name}' already exists")
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    
    return True

def run_migrations():
    """Run database migrations"""
    try:
        import subprocess
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Database migrations completed successfully")
            return True
        else:
            print(f"Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Financial Data Aggregator database...")
    
    # Create database
    if not create_database():
        print("Failed to create database")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("Failed to run migrations")
        sys.exit(1)
    
    print("Database setup completed successfully!")

if __name__ == "__main__":
    main()