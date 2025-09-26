#!/bin/bash

# Environment setup script for Universal Logging Hook Microservice
# Run this to set up the project locally: virtual env, deps, Docker services.

set -e  # Exit on error

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start Docker services (Redis, PostgreSQL)
echo "Starting Docker services..."
docker-compose up -d

# Create database tables (run Python code to init SQLAlchemy models)
echo "Initializing database tables..."
python -c "from src.core.storage import Base, engine; Base.metadata.create_all(bind=engine)"

# Optional: Load sample data or configs
# cp config/development.yml .env  # Uncomment if needed

echo "Setup complete! Run 'source venv/bin/activate' to enter the env."
echo "Start the server with 'python src/main.py'"