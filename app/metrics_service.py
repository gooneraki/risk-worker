"""Prometheus metrics for Risk Worker service"""
import time
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

# Custom metrics for Risk Worker
redis_messages_processed_total = Counter(
    'risk_worker_redis_messages_processed_total',
    'Total Redis messages processed',
    ['channel', 'status']
)

ticker_updates_total = Counter(
    'risk_worker_ticker_updates_total',
    'Total ticker updates processed',
    ['ticker', 'status']
)

price_calculations_duration = Histogram(
    'risk_worker_price_calculations_seconds',
    'Time spent calculating prices and metrics',
    ['ticker']
)

database_writes_total = Counter(
    'risk_worker_database_writes_total',
    'Total database write operations',
    ['table', 'status']
)

active_redis_subscriptions = Gauge(
    'risk_worker_active_redis_subscriptions',
    'Number of active Redis subscriptions'
)

message_queue_size = Gauge(
    'risk_worker_message_queue_size',
    'Size of message processing queue'
)

yfinance_api_calls_total = Counter(
    'risk_worker_yfinance_api_calls_total',
    'Total yFinance API calls',
    ['ticker', 'status']
)

risk_metrics_calculations_total = Counter(
    'risk_worker_risk_metrics_calculations_total',
    'Total risk metrics calculations',
    ['metric_type', 'ticker']
)

worker_errors_total = Counter(
    'risk_worker_errors_total',
    'Total worker errors',
    ['error_type', 'component']
)


def setup_metrics(app):
    """Set up Prometheus metrics instrumentation for FastAPI app"""
    
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/healthz"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="risk_worker_inprogress",
        inprogress_labels=True,
    )
    
    # Add standard metrics
    instrumentator.add(metrics.request_size())
    instrumentator.add(metrics.response_size())
    instrumentator.add(metrics.latency())
    instrumentator.add(metrics.requests())
    
    # Custom metrics for worker endpoints
    @instrumentator.add()
    def track_worker_endpoints(info: metrics.Info):
        endpoint = info.request.url.path
        method = info.request.method
        
        if endpoint.startswith('/trigger-update/'):
            ticker = endpoint.split('/')[-1].upper()
            ticker_updates_total.labels(ticker=ticker, status='triggered').inc()
    
    instrumentator.instrument(app)
    return instrumentator


def track_redis_message(channel: str, status: str = 'success'):
    """Track Redis message processing"""
    redis_messages_processed_total.labels(channel=channel, status=status).inc()


def track_ticker_update(ticker: str, status: str = 'success'):
    """Track ticker update processing"""
    ticker_updates_total.labels(ticker=ticker, status=status).inc()


def track_price_calculation(ticker: str):
    """Decorator to track price calculation time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                price_calculations_duration.labels(ticker=ticker).observe(duration)
        return wrapper
    return decorator


def track_database_write(table: str, status: str = 'success'):
    """Track database write operations"""
    database_writes_total.labels(table=table, status=status).inc()


def update_active_subscriptions(count: int):
    """Update active Redis subscriptions gauge"""
    active_redis_subscriptions.set(count)


def update_message_queue_size(size: int):
    """Update message queue size gauge"""
    message_queue_size.set(size)


def track_yfinance_call(ticker: str, status: str = 'success'):
    """Track yFinance API calls"""
    yfinance_api_calls_total.labels(ticker=ticker, status=status).inc()


def track_risk_calculation(metric_type: str, ticker: str):
    """Track risk metrics calculations"""
    risk_metrics_calculations_total.labels(metric_type=metric_type, ticker=ticker).inc()


def track_worker_error(error_type: str, component: str):
    """Track worker errors"""
    worker_errors_total.labels(error_type=error_type, component=component).inc()


async def metrics_endpoint():
    """Expose Prometheus metrics endpoint"""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    ) 