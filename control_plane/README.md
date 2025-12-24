# Control Plane

FastAPI-based control plane for managing workspaces, connections, jobs, and runs.

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/lakehouse_platform"

# Run migrations
alembic upgrade head

# Start the server
uvicorn api.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register user (dev phase)
- `GET /api/workspaces` - List workspaces
- `POST /api/workspaces` - Create workspace
- `GET /api/connections` - List connections
- `POST /api/connections` - Create connection
- `GET /api/jobs` - List jobs
- `POST /api/jobs` - Create job
- `GET /api/runs` - List runs
- `POST /api/runs` - Create and execute run
- `GET /api/runs/{run_id}` - Get run status

## Development

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run tests (when implemented)
pytest
```

