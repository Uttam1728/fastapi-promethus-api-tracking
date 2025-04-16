# FastAPI Prometheus Middleware Examples

This directory contains examples of how to use the FastAPI Prometheus Middleware package.

## Basic Usage

The `basic_usage.py` file demonstrates the simplest way to use the middleware:

```python
from fastapi import FastAPI
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint

app = FastAPI()

# Add the Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)
```

## Advanced Usage

The `advanced_usage.py` file demonstrates more advanced features:

- Custom prefix for metrics
- Custom logger
- Token usage tracking
- Exception tracking
- Streaming response metrics

## Usage in Cerebrum Project

The `usage_in_cerebrum.py` file demonstrates how to use the middleware in the Cerebrum project:

- Periodic writing of metrics to a file
- Integration with FastAPI lifespan events
- Custom prefix and logger

## Running the Examples

To run any of the examples, use the following command:

```bash
python examples/basic_usage.py
```

Then visit http://localhost:8000/metrics to see the metrics.
