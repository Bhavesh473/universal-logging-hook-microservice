#!/bin/bash

# Run test suite for Universal Logging Hook Microservice
# Assumes pytest for unit/integration tests (install via requirements.txt if needed)
# Focus on core components; full framework by Member B.

set -e

# Activate virtual env if not already
if [ -z "$VIRTUAL_ENV" ]; then
    source venv/bin/activate
fi

# Ensure services are running
docker-compose up -d

# Run unit tests (assuming tests/ folder with pytest files)
echo "Running unit tests..."
pytest tests/unit/core/

# Run integration tests
echo "Running integration tests..."
pytest tests/integration/

# Run load tests (e.g., using locust or simple script; placeholder)
echo "Running load tests..."
# locust -f tests/load/load_test.py --headless -u 100 -r 10 --run-time 1m  # Uncomment if locust installed

echo "All tests completed!"