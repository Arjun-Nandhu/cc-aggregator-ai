#!/bin/bash

# Financial Transaction Aggregator - Quick Start Script
set -e

echo "🏦 Financial Transaction Aggregator - Quick Start"
echo "=================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual configuration!"
    echo "   - Set your Plaid API credentials"
    echo "   - Update database connection string if needed"
    echo "   - Set a secure SECRET_KEY"
    echo ""
fi

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Starting database and Redis services..."
    docker-compose up postgres redis -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
else
    echo "⚠️  Docker not found. Please ensure PostgreSQL and Redis are running manually."
fi

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  No virtual environment detected. Consider activating one:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
    echo ""
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "⚠️  Alembic not found in PATH. Please run migrations manually:"
    echo "   alembic upgrade head"
fi

echo ""
echo "🚀 Starting the application..."
echo "   API will be available at: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📚 To start the background worker (in another terminal):"
echo "   celery -A app.tasks worker --loglevel=info"
echo ""

# Start the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload