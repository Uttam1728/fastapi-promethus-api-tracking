# FastAPI Prometheus Middleware

A middleware for FastAPI applications that tracks and exposes Prometheus metrics.

## Features

- Track request counts, durations, and sizes
- Track response sizes and status codes
- Track errors and exceptions
- Track token usage for LLM applications
- Expose metrics via a FastAPI endpoint
- Stream metrics tracking for streaming responses
- Exception tracking with detailed information

## Installation

### From GitHub (recommended)

Add to your requirements.txt:
```
git+https://github.com/ushankradadiya/fastapi-prometheus-middleware.git
```

Or install directly with pip:
```bash
pip install git+https://github.com/ushankradadiya/fastapi-prometheus-middleware.git
```

### From PyPI (once published)

```bash
pip install fastapi-prometheus-middleware
```

See [INSTALL.md](INSTALL.md) for more installation options.

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

### Streaming Response Metrics

```python
from fastapi import FastAPI
from fastapi_prometheus_middleware import (
    PrometheusMiddleware,
    metrics_endpoint,
    wrap_streaming_response,
    streaming_response_decorator
)

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route('/metrics', metrics_endpoint)

# Option 1: Wrap an existing generator
@app.get("/stream")
async def stream_data():
    async def generator():
        for i in range(10):
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.1)

    # Wrap the generator with metrics tracking
    tracked_generator = wrap_streaming_response(generator(), endpoint="/stream")

    return StreamingResponse(tracked_generator, media_type="text/event-stream")

# Option 2: Use the decorator
@app.get("/stream2")
@streaming_response_decorator(media_type="text/event-stream")
async def stream_data2():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(0.1)
```

### Writing Metrics to a File

```python
import asyncio
from fastapi import FastAPI
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint, generate_prometheus_data

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route('/metrics', metrics_endpoint)

# Write metrics to a file every 10 seconds
async def write_metrics_to_file():
    while True:
        await generate_prometheus_data("metrics.prom")
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(write_metrics_to_file())
```

## Available Metrics

The middleware tracks the following metrics:

- `{prefix}_http_requests_total` - Counter for total HTTP requests
- `{prefix}_http_request_duration_seconds` - Histogram for request duration
- `{prefix}_active_requests` - Gauge for active requests
- `{prefix}_request_size_bytes` - Histogram for request size
- `{prefix}_response_size_bytes` - Histogram for response size
- `{prefix}_errors_total` - Counter for errors
- `{prefix}_token_usage_total` - Counter for token usage
- `{prefix}_exceptions_total` - Counter for exceptions
- `{prefix}_global_exceptions_total` - Counter for global exceptions
- `{prefix}_active_streams` - Gauge for active streaming responses
- `{prefix}_stream_chunks_total` - Counter for streaming chunks
- `{prefix}_stream_bytes_total` - Counter for streaming bytes
- `{prefix}_stream_duration_seconds` - Histogram for stream duration
- `{prefix}_stream_errors_total` - Counter for streaming errors

## License

MIT
