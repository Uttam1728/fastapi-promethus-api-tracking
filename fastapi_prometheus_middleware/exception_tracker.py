"""
Simple utility for tracking exceptions across the application.

This module provides easy-to-use functions for tracking exceptions with Prometheus.
"""

import logging
import inspect
import traceback
from typing import Optional

from fastapi_prometheus_middleware.metrics import APIMetrics
from fastapi_prometheus_middleware.metrics_registry import get_metrics

# Set up logging
logger = logging.getLogger(__name__)


def track_global_exception():
    """
    Increment the global exception counter.
    
    Use this in catch blocks when you just want to count an exception without details.
    
    Example:
        try:
            # Some code that might raise an exception
            result = risky_operation()
        except Exception as e:
            track_global_exception()
            # Handle the exception
    """
    # Get the API metrics instance from the registry
    metrics = get_metrics('api_metrics')
    if not metrics:
        # Fallback to a new instance if not found in registry
        metrics = APIMetrics()
        logger.warning("No API metrics found in registry, using default instance")

    metrics.increment_global_exceptions()


def track_detailed_exception(exception: Exception, status_code: Optional[int] = None):
    """
    Track an exception with detailed information.
    
    This function tracks the exception type, module, and status code.
    
    Args:
        exception: The exception to track
        status_code: The HTTP status code (optional)
        
    Example:
        try:
            # Some code that might raise an exception
            result = risky_operation()
        except Exception as e:
            track_detailed_exception(e, 500)
            # Handle the exception
    """
    try:
        # Get the API metrics instance from the registry
        metrics = get_metrics('api_metrics')
        if not metrics:
            # Fallback to a new instance if not found in registry
            metrics = APIMetrics()
            logger.warning("No API metrics found in registry, using default instance")

        # Track the exception with detailed information
        metrics.track_exception(exception, status_code)

        # Log the exception with traceback
        logger.error(
            f"Exception: {type(exception).__name__}: {str(exception)}",
            extra={
                "traceback": traceback.format_exc(),
                "status_code": status_code
            }
        )
    except Exception as e:
        logger.warning(f"Error tracking detailed exception: {e}")
