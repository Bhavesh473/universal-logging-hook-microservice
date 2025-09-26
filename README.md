# Universal Logging Hook Microservice

## Overview
This project implements a universal logging microservice that can hook into any application for centralized logging. It supports log ingestion via API, processing (normalization, timestamping), queuing in Redis, persistent storage in PostgreSQL, event ordering with sequence numbers, checkpoint management, and log replay. The service is built with FastAPI for the HTTP server and is containerized with Docker.

The project is divided between two members:
- **Member A (Sumitra)**: Core service development (API, processing, storage, security, performance, containerization).
- **Member B (Bhavesh)**: Integration and operations (client libraries, auto-discovery, monitoring, testing, documentation, deployment support).

This split allows parallel development with clear integration points via API contracts.

## Features
- **API Endpoints**: `/logs` (POST for log ingestion), `/checkpoint` (POST for snapshots), `/replay/{checkpoint_id}` (GET for replay).
- **Storage**: Redis for queuing and sequencing, PostgreSQL for persistence.
- **Security**: API key authentication.
- **Optimization**: Async processing with background tasks.
- **Integration**: Multi-language client libraries (Python, Node.js, PHP), legacy forwarding, auto-discovery.
- **Ops**: Monitoring, testing framework, deployment templates.

## Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Git

## Setup
1. Clone the repository: https://github.com/Bhavesh473/universal-logging-hook-microservice.git

2. Create and activate virtual environment: python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies: pip install -r requirements.txt

4. Configure environment: Copy `config/development.yml` values to `.env` or set directly (e.g., POSTGRES_URI, REDIS_HOST, API_KEY).

5. Start services: docker-compose up -d

6. Initialize database (runs SQLAlchemy table creation): python -c "from src.core.storage import Base, engine; Base.metadata.create_all(bind=engine)"

## Running the Service
- Local: `python src/main.py` (runs on http://localhost:8000)
- Docker: `docker-compose up --build`
- Access Swagger docs: http://localhost:8000/docs

## Testing
- Run tests: `./scripts/test.sh`
- Use Postman or Swagger to test endpoints (include X-API-KEY header).

## Deployment
- Build and deploy: `./scripts/deploy.sh` (customize for your registry/K8s).
- See `docs/deployment.md` for details.

## Directory Structure
- `src/core/`: Core components (API, processor, storage, security).
- `src/integration/`: Integration tools and client libraries.
- `config/`: Environment configs.
- `tests/`: Test suites.
- `docs/`: Documentation.
- `scripts/`: Automation scripts.

## Contributing
- Member A: Focus on core/.
- Member B: Focus on integration/.
- Use single repo; combine in `main.py`.

For full architecture, see `docs/architecture.md`. For integration, see `docs/integration-guide.md`.
