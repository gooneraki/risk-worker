# Risk Worker

FastAPI microservice that processes stock ticker updates in real-time.

## What it does

- Subscribes to Redis `ticker_updates` channel
- Fetches current stock prices from yFinance
- Stores price data in database
- Provides REST API for price queries

## Quick Start

### Local Development
```bash
# Copy environment file
cp env.example .env

# Start locally (SQLite + FakeRedis)
.\local_start.ps1
# Choose "L" for local
```

### Docker Deployment
```bash
# Copy environment files
cp env.example .env.docker.postgres
cp env.example .env.docker.worker

# Edit the .env.docker.* files with appropriate values
# Then start with Docker
.\local_start.ps1
# Choose "D" for Docker
```

## API Endpoints

- `GET /healthz` - Health check
- `GET /latest-price/{ticker}` - Get latest price for ticker (e.g., `/latest-price/AAPL`)
- `POST /trigger-update/{ticker}` - Manually trigger price update

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/risk_worker.db

# API Server
API_HOST=127.0.0.1
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## Usage

### Test the API
```bash
# Check health
curl http://localhost:8000/healthz

# Get latest price
curl http://localhost:8000/latest-price/AAPL

# Trigger manual update
curl -X POST http://localhost:8000/trigger-update/AAPL
```

### Send ticker updates via Redis
```bash
# Connect to Redis
redis-cli

# Send ticker update
PUBLISH ticker_updates "AAPL"

# Or JSON format
PUBLISH ticker_updates '{"ticker": "AAPL", "action": "add"}'
```

## Docker Commands

```bash
# Start services
docker-compose up -d --build

# View logs
docker-compose logs -f risk-worker

# Stop services
docker-compose down
```

## Architecture

- **FastAPI** - Web framework
- **SQLModel** - Database ORM
- **PostgreSQL** - Production database
- **Redis** - Pub/sub messaging
- **yFinance** - Stock price data 