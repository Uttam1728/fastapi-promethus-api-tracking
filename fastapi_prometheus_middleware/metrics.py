"""
Prometheus metrics for API monitoring.

This module defines a class for tracking API performance and usage metrics.
"""

import logging
import inspect
from typing import Dict, Any, Optional, List, Union

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, REGISTRY
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client import generate_latest

# Set up logging
logger = logging.getLogger(__name__)


class APIMetrics:
    """
    Class for tracking API metrics using Prometheus.

    This class provides methods for tracking various aspects of API requests,
    including request counts, durations, sizes, and errors.
    """
    
    def __init__(self, prefix: str = 'fastapi'):
        """
        Initialize the API metrics with the given prefix.

        Args:
            prefix: Prefix for all metric names (default: 'fastapi')
        """
        self.prefix = prefix

        # Define Prometheus metrics with safe creation to avoid duplicates
        self.http_request_counter = self._create_or_get_counter(
            f'{prefix}_http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code']
        )

        self.http_request_duration = self._create_or_get_histogram(
            f'{prefix}_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, 75.0, 100.0)
        )

        self.active_requests = self._create_or_get_gauge(
            f'{prefix}_active_requests',
            'Number of active requests',
            ['method', 'endpoint']
        )

        self.request_size = self._create_or_get_histogram(
            f'{prefix}_request_size_bytes',
            'Request size in bytes',
            ['method', 'endpoint'],
            buckets=(10, 100, 1000, 10000, 100000, 1000000)
        )

        self.response_size = self._create_or_get_histogram(
            f'{prefix}_response_size_bytes',
            'Response size in bytes',
            ['method', 'endpoint', 'status_code'],
            buckets=(10, 100, 1000, 10000, 100000, 1000000)
        )

        self.error_counter = self._create_or_get_counter(
            f'{prefix}_errors_total',
            'Total number of errors',
            ['method', 'endpoint', 'error_type']
        )

        self.token_usage = self._create_or_get_counter(
            f'{prefix}_token_usage_total',
            'Total number of tokens used',
            ['type']  # 'input', 'output', 'total'
        )

        # Add exception counter for tracking exceptions in different parts of the application
        self.exception_counter = self._create_or_get_counter(
            f'{prefix}_exceptions_total',
            'Total number of exceptions',
            ['exception_type', 'module', 'code']
        )

        # Add a global exception counter for tracking total exceptions across the application
        # This counter has no labels to ensure it's a single global counter
        self.global_exception_counter = self._create_or_get_counter(
            f'{prefix}_global_exceptions_total',
            'Total number of exceptions across the entire application',
            []
        )

    def _create_or_get_counter(self, name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Counter:
        """
        Create a new Counter or return an existing one with the same name.
        
        Args:
            name: Metric name
            documentation: Metric documentation
            labelnames: List of label names
            
        Returns:
            A Counter object
        """
        try:
            return Counter(name, documentation, labelnames or [])
        except ValueError:
            # If the counter already exists, get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a slightly different name
            return Counter(f"{name}_new", documentation, labelnames or [])

    def _create_or_get_histogram(self, name: str, documentation: str, labelnames: Optional[List[str]] = None, buckets: Optional[tuple] = None) -> Histogram:
        """
        Create a new Histogram or return an existing one with the same name.
        
        Args:
            name: Metric name
            documentation: Metric documentation
            labelnames: List of label names
            buckets: Histogram buckets
            
        Returns:
            A Histogram object
        """
        try:
            return Histogram(name, documentation, labelnames or [], buckets=buckets)
        except ValueError:
            # If the histogram already exists, get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a slightly different name
            return Histogram(f"{name}_new", documentation, labelnames or [], buckets=buckets)

    def _create_or_get_gauge(self, name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Gauge:
        """
        Create a new Gauge or return an existing one with the same name.
        
        Args:
            name: Metric name
            documentation: Metric documentation
            labelnames: List of label names
            
        Returns:
            A Gauge object
        """
        try:
            return Gauge(name, documentation, labelnames or [])
        except ValueError:
            # If the gauge already exists, get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a slightly different name
            return Gauge(f"{name}_new", documentation, labelnames or [])

    def _get_endpoint(self, request: Request) -> str:
        """
        Get the endpoint path from the request.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            The endpoint path
        """
        route = getattr(request.scope.get('route'), 'path', None)
        if route:
            return route
        
        # Fallback to the request path if route is not available
        return request.url.path

    def _safe_labels(self, metric: Any, labels: Dict[str, str]) -> Any:
        """
        Safely apply labels to a metric, handling any errors.
        
        Args:
            metric: The metric to label
            labels: Dictionary of label names and values
            
        Returns:
            The labeled metric or None if an error occurred
        """
        try:
            return metric.labels(**labels)
        except (KeyError, ValueError) as e:
            logger.warning(f"Error applying labels to metric: {e}")
            return None

    def track_request_started(self, request: Request, request_body_size: int) -> None:
        """
        Track the start of a request.

        Args:
            request: The FastAPI request object
            request_body_size: Size of the request body in bytes
        """
        try:
            method = request.method
            endpoint = self._get_endpoint(request)

            # Track request size
            labeled_metric = self._safe_labels(self.request_size, {"method": method, "endpoint": endpoint})
            if labeled_metric:
                labeled_metric.observe(request_body_size)

            # Increment active requests gauge
            labeled_metric = self._safe_labels(self.active_requests, {"method": method, "endpoint": endpoint})
            if labeled_metric:
                labeled_metric.inc()
        except Exception as e:
            logger.warning(f"Error tracking request start: {e}")

    def track_request_completed(self, request: Request, response: Response, duration: float) -> None:
        """
        Track a completed request.

        Args:
            request: The FastAPI request object
            response: The response object
            duration: Request duration in seconds
        """
        try:
            method = request.method
            endpoint = self._get_endpoint(request)
            status_code = str(response.status_code)

            # Record request duration
            labeled_metric = self._safe_labels(self.http_request_duration, {"method": method, "endpoint": endpoint})
            if labeled_metric:
                labeled_metric.observe(duration)

            # Count request
            labeled_metric = self._safe_labels(self.http_request_counter,
                                             {"method": method, "endpoint": endpoint, "status_code": status_code})
            if labeled_metric:
                labeled_metric.inc()

            # Track response size if available
            if hasattr(response, 'body') and response.body:
                response_size = len(response.body)
                labeled_metric = self._safe_labels(self.response_size,
                                                 {"method": method, "endpoint": endpoint, "status_code": status_code})
                if labeled_metric:
                    labeled_metric.observe(response_size)
        except Exception as e:
            logger.warning(f"Error tracking request completion: {e}")

    def track_request_error(self, request: Request, status_code: int, error_type: str, duration: float) -> None:
        """
        Track a request that resulted in an error.

        Args:
            request: The FastAPI request object
            status_code: The HTTP status code
            error_type: The type of error
            duration: Request duration in seconds
        """
        try:
            method = request.method
            endpoint = self._get_endpoint(request)
            status_code_str = str(status_code)

            # Record request duration
            labeled_metric = self._safe_labels(self.http_request_duration, {"method": method, "endpoint": endpoint})
            if labeled_metric:
                labeled_metric.observe(duration)

            # Count request
            labeled_metric = self._safe_labels(self.http_request_counter,
                                             {"method": method, "endpoint": endpoint, "status_code": status_code_str})
            if labeled_metric:
                labeled_metric.inc()

            # Count error
            labeled_metric = self._safe_labels(self.error_counter,
                                             {"method": method, "endpoint": endpoint, "error_type": error_type})
            if labeled_metric:
                labeled_metric.inc()
        except Exception as e:
            logger.warning(f"Error tracking request error: {e}")

    def track_request_finished(self, request: Request) -> None:
        """
        Track the end of a request (decrement active requests).

        Args:
            request: The FastAPI request object
        """
        try:
            method = request.method
            endpoint = self._get_endpoint(request)

            # Decrement active requests gauge
            labeled_metric = self._safe_labels(self.active_requests, {"method": method, "endpoint": endpoint})
            if labeled_metric:
                labeled_metric.dec()
        except Exception as e:
            logger.warning(f"Error tracking request finish: {e}")

    def track_token_usage(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0) -> None:
        """
        Track token usage for LLM applications.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total number of tokens
        """
        try:
            # Track input tokens
            labeled_metric = self._safe_labels(self.token_usage, {"type": "input"})
            if labeled_metric:
                labeled_metric.inc(input_tokens)

            # Track output tokens
            labeled_metric = self._safe_labels(self.token_usage, {"type": "output"})
            if labeled_metric:
                labeled_metric.inc(output_tokens)

            # Track total tokens
            labeled_metric = self._safe_labels(self.token_usage, {"type": "total"})
            if labeled_metric:
                labeled_metric.inc(total_tokens)
        except Exception as e:
            logger.warning(f"Error tracking token usage: {e}")

    def track_exception(self, exception: Exception, status_code: Optional[int] = None) -> None:
        """
        Track an exception with detailed information.

        Args:
            exception: The exception to track
            status_code: The HTTP status code (optional)
        """
        try:
            # Get exception details
            exception_type = type(exception).__name__
            
            # Get the module where the exception occurred
            frame = inspect.trace()[-1]
            module = frame.frame.f_globals.get('__name__', 'unknown')
            
            # Use status code as code if available, otherwise use 0
            code = str(status_code) if status_code is not None else "0"
            
            # Increment exception counter
            labeled_metric = self._safe_labels(self.exception_counter, {
                "exception_type": exception_type,
                "module": module,
                "code": code
            })
            if labeled_metric:
                labeled_metric.inc()
        except Exception as e:
            logger.warning(f"Error tracking exception: {e}")

    def increment_global_exceptions(self) -> None:
        """
        Increment the global exception counter.
        """
        try:
            self.global_exception_counter.inc()
        except Exception as e:
            logger.warning(f"Error incrementing global exception counter: {e}")


# Create a singleton instance for easy import
api_metrics = APIMetrics()

# Export the instance methods as module-level functions for backward compatibility
track_request_started = api_metrics.track_request_started
track_request_completed = api_metrics.track_request_completed
track_request_error = api_metrics.track_request_error
track_request_finished = api_metrics.track_request_finished
track_token_usage = api_metrics.track_token_usage
track_exception = api_metrics.track_exception
increment_global_exceptions = api_metrics.increment_global_exceptions


async def metrics_endpoint(request=None):
    """
    Endpoint for exposing Prometheus metrics.

    Args:
        request: The FastAPI request object (optional)

    Returns:
        Response: A response containing the latest Prometheus metrics.
    """
    from fastapi import Response
    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
