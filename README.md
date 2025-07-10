# Risk Worker

A FastAPI-based microservice for processing real-time stock price updates via Redis Pub/Sub and storing them in PostgreSQL.

## Architecture

- **FastAPI** - Async web framework with REST API endpoints
- **SQLModel** - Database ORM with async support
- **PostgreSQL** - Primary data store with async driver (asyncpg)
- **Redis** - Pub/Sub messaging for ticker updates
- **yFinance** - Real-time stock price data source
- **Docker** - Containerized deployment

## Features

- Real-time ticker price processing via Redis Pub/Sub
- Async database operations with connection pooling
- REST API for price queries and manual triggers
- Automatic ticker metadata management
- Health check endpoint
- Comprehensive error handling and logging

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Run with Docker
```bash
# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/healthz

# Get latest price for a ticker
curl http://localhost:8000/latest-price/AAPL

# Manually trigger price update
curl -X POST http://localhost:8000/trigger-update/AAPL
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/risk_metrics"
export REDIS_URL="redis://localhost:6379"

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/healthz` | Health check |
| GET | `/latest-price/{ticker}` | Get latest price for ticker |
| POST | `/trigger-update/{ticker}` | Manually trigger price update |

## Database Schema

### TickerPrice
- `id` - Primary key
- `ticker` - Stock symbol (indexed)
- `price` - Current price
- `volume` - Trading volume
- `market_cap` - Market capitalization
- `timestamp` - Price timestamp
- `created_at` - Record creation time

### TickerMetadata
- `id` - Primary key
- `ticker` - Stock symbol (unique, indexed)
- `company_name` - Company name
- `sector` - Business sector
- `industry` - Industry classification
- `last_updated` - Metadata update timestamp

## Redis Integration

The service subscribes to the `ticker_updates` channel and processes incoming ticker symbols by:
1. Fetching current price from yFinance
2. Storing price data in PostgreSQL
3. Updating ticker metadata if needed

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (default: INFO)

## Development

### Project Structure
```
app/
├── main.py          # FastAPI application and Redis subscriber
├── models.py        # SQLModel database models
├── schemas.py       # Pydantic schemas for API responses
├── metrics.py       # Core business logic for price processing
└── database.py      # Database configuration and session management
```

### Dependencies
High-level dependencies (see `high-requirements.txt`):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlmodel` - Database ORM
- `asyncpg` - PostgreSQL async driver
- `redis` - Redis client
- `yfinance` - Stock data API
- `python-dotenv` - Environment configuration

### Code Quality
- Async/await patterns throughout
- Type hints with SQLModel
- Comprehensive error handling
- Structured logging
- Pylint configuration included

## Deployment

The service is containerized and includes:
- Multi-stage Docker build
- Health checks for all services
- Volume persistence for PostgreSQL
- Automatic restart policies
- Service dependency management

## Monitoring

- Health check endpoint at `/healthz`
- Structured logging with correlation IDs
- Database connection monitoring
- Redis subscription status tracking 