"""
Utilities for creating FastAPI StreamingResponse objects with Prometheus metrics tracking.

This module provides functions for creating streaming responses that automatically track metrics.
"""

import inspect
import logging
from typing import AsyncGenerator, Any, Optional, Dict, Union

from fastapi import Response
from starlette.responses import StreamingResponse

from fastapi_prometheus_middleware.streaming_wrapper import StreamingMetricsWrapper

# Set up logging
logger = logging.getLogger(__name__)


def create_streaming_response(
    generator: AsyncGenerator[Any, None],
    media_type: str = "text/event-stream",
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    background: Optional[Any] = None,
    endpoint: Optional[str] = None
) -> StreamingResponse:
    """
    Create a StreamingResponse with Prometheus metrics tracking.

    This function wraps the generator with metrics tracking and creates a StreamingResponse.

    Args:
        generator: The async generator that produces the response content
        media_type: The media type of the response (default: "text/event-stream")
        status_code: The HTTP status code (default: 200)
        headers: Additional headers to include in the response
        background: Background tasks to run after the response is sent
        endpoint: The endpoint path or name (default: auto-detected)

    Returns:
        A StreamingResponse object with metrics tracking
    """
    # Determine the endpoint name if not provided
    if endpoint is None:
        try:
            # Get the caller's frame
            frame = inspect.currentframe().f_back
            if frame:
                # Try to get the function name
                func_name = frame.f_code.co_name
                # Try to get the class name if it's a method
                if 'self' in frame.f_locals:
                    class_name = frame.f_locals['self'].__class__.__name__
                    endpoint = f"{class_name}.{func_name}"
                else:
                    endpoint = func_name
            else:
                endpoint = "unknown"
        except Exception as e:
            logger.warning(f"Error getting caller endpoint: {e}")
            endpoint = "unknown"

    # Wrap the generator with metrics tracking
    metrics_generator = StreamingMetricsWrapper(generator, endpoint)

    # Create and return the StreamingResponse
    return StreamingResponse(
        metrics_generator,
        media_type=media_type,
        status_code=status_code,
        headers=headers,
        background=background
    )


def streaming_response_decorator(
    media_type: str = "text/event-stream",
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    endpoint: Optional[str] = None
):
    """
    Decorator for creating endpoint functions that return StreamingResponse with metrics tracking.

    Args:
        media_type: The media type of the response (default: "text/event-stream")
        status_code: The HTTP status code (default: 200)
        headers: Additional headers to include in the response
        endpoint: The endpoint path or name (default: auto-detected)

    Returns:
        A decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get the generator from the original function
            generator = await func(*args, **kwargs)

            # Determine the endpoint name
            endpoint_name = endpoint
            if endpoint_name is None:
                if hasattr(func, "__qualname__"):
                    endpoint_name = func.__qualname__
                else:
                    endpoint_name = func.__name__

            # Create and return the StreamingResponse
            return create_streaming_response(
                generator,
                media_type=media_type,
                status_code=status_code,
                headers=headers,
                endpoint=endpoint_name
            )

        return wrapper

    return decorator


def create_metrics_streaming_response(
    generator: AsyncGenerator[Any, None],
    media_type: str = "text/event-stream",
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    endpoint: Optional[str] = None
) -> StreamingResponse:
    """
    Create a StreamingResponse with Prometheus metrics tracking.

    This is an alias for create_streaming_response for backward compatibility.

    Args:
        generator: The async generator that produces the response content
        media_type: The media type of the response (default: "text/event-stream")
        status_code: The HTTP status code (default: 200)
        headers: Additional headers to include in the response
        endpoint: The endpoint path or name (default: auto-detected)

    Returns:
        A StreamingResponse with metrics tracking
    """
    return create_streaming_response(
        generator,
        media_type=media_type,
        status_code=status_code,
        headers=headers,
        endpoint=endpoint
    )
