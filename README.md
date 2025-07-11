# Risk Worker

**Async microservice worker** for processing real-time stock ticker updates. Part of a larger risk management system.

## Overview

This worker service:
- Subscribes to Redis `ticker_updates` channel
- Fetches current prices from yFinance API
- Stores ticker data in PostgreSQL
- Provides REST API for latest price queries

**Architecture**: FastAPI + SQLModel + PostgreSQL + Redis + Docker

## Quick Start

### Local Development (SQLite + FakeRedis)
```bash
python run.py --local
```

### Docker Mode (PostgreSQL + Redis)
```bash
python run.py --docker
```

### Interactive Mode
```bash
python run.py  # Choose local or docker
```

## Configuration

Copy and customize environment file:
```bash
cp environment.example .env.local     # For local development
cp environment.example .env.production # For docker
```

**Key settings**:
- `DATABASE_URL` - PostgreSQL connection string
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `WORKER_NAME` - Instance identifier
- `API_HOST/API_PORT` - Server binding

## Testing

### Local Testing
```bash
# Start worker locally
python run.py --local

# Test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/latest-price/AAPL

# Trigger manual update
curl -X POST http://localhost:8000/trigger-update/AAPL
```

### Docker Testing
```bash
# Start all services
python run.py --docker

# Test from outside container
curl http://localhost:8000/healthz
curl http://localhost:8000/latest-price/MSFT
```

## Docker Commands

### Essential Commands
```bash
# Start all services
docker-compose up -d --build

# View logs (most useful)
docker-compose logs -f risk-worker
docker-compose logs -f risk-postgres
docker-compose logs -f redis

# Service status
docker-compose ps

# Stop all services
docker-compose down
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d risk_worker

# Common SQL queries
\dt                              # List tables
SELECT * FROM tickerprice LIMIT 5;
SELECT ticker, price, timestamp FROM tickerprice ORDER BY timestamp DESC LIMIT 10;
```

### Redis Access
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Monitor ticker updates
MONITOR

# Publish test ticker
PUBLISH ticker_updates "AAPL"
```

### Container Shell Access
```bash
# Access worker container
docker-compose exec risk-worker bash

# Access postgres container
docker-compose exec postgres bash

# Access redis container
docker-compose exec redis sh
```

## Logs

### Log Locations
- **Local**: `logs/risk-worker.log`
- **Docker**: `docker-compose logs -f risk-worker`

### Log Rotation
- Max file size: 1MB
- Backup count: 10 files
- Format: `timestamp - name - level - message`

### Useful Log Commands
```bash
# Follow logs in real-time
docker-compose logs -f risk-worker

# View last 50 lines
docker-compose logs --tail=50 risk-worker

# View logs since timestamp
docker-compose logs --since="2024-01-01T00:00:00Z" risk-worker
```

## Database Schema

### TickerPrice Table
```sql
CREATE TABLE tickerprice (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION,
    market_cap DOUBLE PRECISION,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_tickerprice_ticker ON tickerprice (ticker);
```

### TickerMetadata Table
```sql
CREATE TABLE tickermetadata (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR UNIQUE NOT NULL,
    company_name VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    last_updated TIMESTAMP NOT NULL
);
CREATE INDEX ix_tickermetadata_ticker ON tickermetadata (ticker);
```

## API Endpoints

- `GET /healthz` - Health check
- `GET /latest-price/{ticker}` - Get latest price for ticker
- `POST /trigger-update/{ticker}` - Manual price update

## Integration with Bigger System

This worker is designed to be part of a larger risk management system:

1. **Upstream**: Receives ticker symbols via Redis pub/sub
2. **Downstream**: Provides price data via REST API
3. **Storage**: Maintains historical price data in PostgreSQL
4. **Monitoring**: Exposes health check and metrics endpoints

### Redis Integration
```python
# Publish ticker update (from main system)
redis_client.publish("ticker_updates", "AAPL")
```

### Database Integration
```python
# Query latest prices (from other services)
SELECT ticker, price, timestamp 
FROM tickerprice 
WHERE ticker = 'AAPL' 
ORDER BY timestamp DESC 
LIMIT 1;
```

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check if ports are available
netstat -an | grep :8000
netstat -an | grep :5432
netstat -an | grep :6379

# Check environment file
cat .env.local  # or .env.production
```

**Database connection issues**:
```bash
# Test PostgreSQL connection
docker-compose exec postgres pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

**Redis connection issues**:
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

**No price data**:
```bash
# Test yFinance manually
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info.get('regularMarketPrice'))"

# Check worker logs
docker-compose logs -f risk-worker
```

## Development Notes

- Uses async/await throughout for better performance
- Automatic Redis fallback to FakeRedis for local development
- Database migrations handled by SQLModel
- Configurable logging with rotation
- Health checks for all Docker services
- Graceful shutdown handling 