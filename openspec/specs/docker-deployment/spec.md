# docker-deployment

## Purpose

Containerized deployment. Provides Dockerfile and Docker Compose configuration for one-command startup, with persistent storage for skill configurations and environment-variable-based configuration.

## Requirements

### Requirement: Dockerfile for single-container deployment

The project SHALL include a `Dockerfile` that builds the application into a single Docker image with all dependencies.

#### Scenario: Build Docker image

- **WHEN** user runs `docker build -t chatrobot .`
- **THEN** the image SHALL build successfully with Python dependencies installed and application code copied

#### Scenario: Container starts successfully

- **WHEN** user runs `docker run -p 8000:8000 --env-file .env chatrobot`
- **THEN** the FastAPI server SHALL start and listen on port 8000

### Requirement: Docker Compose for one-click deployment

The project SHALL include a `docker-compose.yml` that defines the service, port mapping, environment file, and volume mounts for persistent data.

#### Scenario: One-click start with docker compose

- **WHEN** user runs `docker compose up -d` with a valid `.env` file
- **THEN** the service SHALL start in detached mode, the admin UI SHALL be accessible at `http://localhost:8000`, and the Feishu webhook SHALL be ready at `http://localhost:8000/api/feishu/event`

#### Scenario: Persistent skill data across restarts

- **WHEN** user creates skills via the Web UI and restarts the container
- **THEN** all skill configurations SHALL be preserved via the mounted SQLite database volume

### Requirement: Environment variable configuration

The project SHALL include a `.env.example` file documenting all required and optional environment variables.

#### Scenario: First-time setup

- **WHEN** a new user copies `.env.example` to `.env` and fills in the values
- **THEN** they SHALL have all necessary configuration to start the bot

### Requirement: Health check endpoint

The application SHALL expose a health check endpoint for Docker health monitoring.

#### Scenario: Health check returns OK

- **WHEN** Docker sends a health check request to `/api/health`
- **THEN** the endpoint SHALL return HTTP 200 with `{"status": "ok"}` if all services are functional
