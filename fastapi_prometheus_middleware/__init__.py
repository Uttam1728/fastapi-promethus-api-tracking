"""
FastAPI Prometheus Middleware

A middleware for FastAPI applications that tracks and exposes Prometheus metrics.
"""

from fastapi_prometheus_middleware.middleware import PrometheusMiddleware
from fastapi_prometheus_middleware.metrics import metrics_endpoint, APIMetrics
from fastapi_prometheus_middleware.exception_tracker import (
    track_detailed_exception,
    track_global_exception
)
from fastapi_prometheus_middleware.streaming_metrics import StreamingMetrics
from fastapi_prometheus_middleware.metrics_registry import (
    register_metrics,
    get_metrics,
    get_all_metrics
)
from fastapi_prometheus_middleware.streaming_wrapper import (
    StreamingMetricsWrapper,
    wrap_streaming_response,
    streaming_metrics_decorator,
    track_streaming_generator
)
from fastapi_prometheus_middleware.streaming_response import (
    create_streaming_response,
    streaming_response_decorator,
    create_metrics_streaming_response
)
from fastapi_prometheus_middleware.helper import generate_prometheus_data

__version__ = "0.1.0"
