# Risk Worker

FastAPI microservice that processes stock ticker updates in real-time.

## Features

- Subscribes to Redis `ticker_updates` channel
- Fetches current stock prices from yFinance
- Stores price data in database
- Provides REST API for price queries

## Quick Start

```bash
# Copy environment file
cp env.example .env

# Start locally (SQLite + FakeRedis)
.\local_start.ps1
```

## API Endpoints

- `GET /healthz` - Health check
- `GET /latest-price/{ticker}` - Get latest price for ticker
- `POST /trigger-update/{ticker}` - Manually trigger price update

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/risk_worker.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Worker Security
WORKER_SECRET=your-shared-secret-key-change-this
```

## Usage

```bash
# Test the API
curl http://localhost:8000/healthz
curl http://localhost:8000/latest-price/AAPL
curl -X POST http://localhost:8000/trigger-update/AAPL

# Send ticker updates via Redis
redis-cli
PUBLISH ticker_updates "AAPL"
``` 