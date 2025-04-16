# FastAPI Prometheus Middleware

A middleware for FastAPI applications that tracks and exposes Prometheus metrics.

## Features

- Track request counts, durations, and sizes
- Track response sizes and status codes
- Track errors and exceptions
- Track token usage for LLM applications
- Expose metrics via a FastAPI endpoint

## Installation

```bash
pip install fastapi-prometheus-middleware
```

## Usage

### Basic Usage

```python
from fastapi import FastAPI
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint

app = FastAPI()

# Add the Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)
```

### Advanced Usage

```python
from fastapi import FastAPI
import logging
from fastapi_prometheus_middleware import (
    PrometheusMiddleware, 
    metrics_endpoint,
    track_detailed_exception,
    track_global_exception
)
from fastapi_prometheus_middleware.context import token_usage_context

# Set up logging
logger = logging.getLogger(__name__)

app = FastAPI()

# Add the Prometheus middleware with custom configuration
app.add_middleware(
    PrometheusMiddleware,
    prefix="myapp",  # Custom prefix for metrics
    skip_paths=["/metrics", "/health"],  # Paths to skip tracking
    logger=logger  # Custom logger
)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)

# Track token usage in your LLM application
@app.post("/generate")
async def generate_text(prompt: str):
    # Your LLM code here
    
    # Track token usage
    token_data = token_usage_context.get()
    token_data["input_tokens"] = 10  # Replace with actual values
    token_data["output_tokens"] = 20  # Replace with actual values
    token_data["total_tokens"] = 30  # Replace with actual values
    token_usage_context.set(token_data)
    
    return {"text": "Generated text"}

# Track exceptions
@app.get("/risky")
async def risky_operation():
    try:
        # Some risky operation
        result = 1 / 0
    except Exception as e:
        # Track the exception
        track_detailed_exception(e, 500)
        return {"error": "An error occurred"}
```

## Available Metrics

The middleware exposes the following metrics:

- `{prefix}_http_requests_total`: Total number of HTTP requests
- `{prefix}_http_request_duration_seconds`: HTTP request duration in seconds
- `{prefix}_active_requests`: Number of active requests
- `{prefix}_request_size_bytes`: Request size in bytes
- `{prefix}_response_size_bytes`: Response size in bytes
- `{prefix}_errors_total`: Total number of errors
- `{prefix}_token_usage_total`: Total number of tokens used (for LLM applications)
- `{prefix}_exceptions_total`: Total number of exceptions
- `{prefix}_global_exceptions_total`: Total number of exceptions across the entire application

## License

MIT
