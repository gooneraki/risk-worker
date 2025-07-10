# Risk Worker

A FastAPI-based microservice for processing real-time stock price updates via Redis Pub/Sub and storing them in PostgreSQL.

## Architecture

- **FastAPI** - Async web framework with REST API endpoints
- **SQLModel** - Database ORM with async support
- **PostgreSQL** - Primary data store with async driver (asyncpg)
- **Redis** - Pub/Sub messaging for ticker updates
- **yFinance** - Real-time stock price data source
- **Docker** - Containerized deployment

## Quick Start

### **🚀 One Command Setup**

```bash
# Clone and setup
git clone <your-repo>
cd risk-worker
pip install -r requirements.txt

# Run (automatically creates .env and runs!)
python run.py
```

**That's it!** The script automatically:
- ✅ **Detects** your environment (PostgreSQL/Redis availability)
- ✅ **Creates** a `.env` file with optimal configuration
- ✅ **Starts** Docker services if needed
- ✅ **Launches** your application with the right settings

### **🐳 Docker Commands**

```bash
# Start everything
docker-compose up -d --build

# Start services only (for development)
python run.py --services-only

# Check status
docker-compose ps

# View logs (most useful!)
docker-compose logs -f risk-worker
docker-compose logs -f postgres
docker-compose logs -f redis

# Get shell access
docker-compose exec risk-worker bash
docker-compose exec postgres psql -U postgres -d risk_worker
docker-compose exec redis redis-cli

# Stop everything
docker-compose down
```

### **🔧 Development Workflow**

```bash
# Option 1: All-in-one (first time)
python run.py  # Auto-creates .env, starts Docker + app

# Option 2: Services-first workflow
python run.py --services-only  # Start PostgreSQL + Redis
python run.py                  # Uses existing .env, starts app

# Option 3: Force local SQLite mode
python run.py --local
```

## Configuration

The project uses a **smart `.env` file system** with automatic environment detection:

1. **First run**: `python run.py` detects your environment and creates optimal `.env`
2. **Customization**: Edit `.env` file to override any setting
3. **Template**: Copy `environment.example` for manual setup

### **Configuration Modes**

| Mode | Database | Redis | Created by |
|------|----------|-------|------------|
| **Docker** | PostgreSQL | Real Redis | `python run.py` (default) |
| **Local** | SQLite | FakeRedis | `python run.py --local` |
| **Production** | PostgreSQL | Real Redis | `docker-compose up -d` |

### **Manual Configuration**

```bash
# Copy template and customize
cp environment.example .env
edit .env                    # Customize any setting
python run.py               # Uses your custom .env
```

## API Endpoints

### Health Check
```bash
GET /healthz
# Returns: {"status": "healthy", "timestamp": "..."}
```

### Get Latest Price
```bash
GET /price/{ticker}
# Example: GET /price/AAPL
# Returns: {"ticker": "AAPL", "price": 150.25, "timestamp": "..."}
```

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

## Development

### Project Structure
```
app/
├── main.py          # FastAPI application and Redis subscriber
├── models.py        # SQLModel database models
├── schemas.py       # Pydantic schemas for API responses
├── metrics.py       # Core business logic for price processing
├── database.py      # Database configuration and session management
└── config.py        # Settings loaded from .env file
```

### Dependencies
High-level dependencies (see `requirements.txt`):
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
- Structured logging with automatic rotation (10MB files, 10 backups)
- Pylint configuration included

## Deployment

### Local Development
```bash
python run.py                  # Auto-creates .env, detects environment
python run.py --services-only  # Start services only, useful for testing
python run.py --local          # Force SQLite mode
```

### Production
```bash
docker-compose up -d  # Full containerized stack
```

The service is containerized and includes:
- Multi-stage Docker build
- Health checks for all services
- Volume persistence for PostgreSQL
- Automatic restart policies
- Service dependency management

## Troubleshooting

```bash
# Check what's running
docker-compose ps

# View real-time logs
docker-compose logs -f risk-worker

# Test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/price/AAPL

# Access database
docker-compose exec postgres psql -U postgres -d risk_worker

# Check configuration
cat .env

# Reset configuration
rm .env && python run.py
``` 