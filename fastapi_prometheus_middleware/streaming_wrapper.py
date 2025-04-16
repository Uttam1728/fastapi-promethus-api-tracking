"""
Wrapper for streaming responses to track Prometheus metrics.

This module provides utilities for wrapping streaming generators with metrics tracking.
"""

import time
import inspect
import logging
from typing import AsyncGenerator, Any, Optional, Callable, Union

from fastapi_prometheus_middleware.streaming_metrics import (
    track_stream_started,
    track_stream_chunk,
    track_stream_finished,
    track_stream_error
)

# Set up logging
logger = logging.getLogger(__name__)


class StreamingMetricsWrapper:
    """
    Wrapper for streaming generators that tracks Prometheus metrics.

    This class wraps an async generator and tracks metrics for:
    - Stream start and end
    - Chunks sent
    - Stream duration
    - Errors
    """

    def __init__(self, generator, endpoint: Optional[str] = None):
        """
        Initialize the wrapper with a generator and endpoint.

        Args:
            generator: The async generator to wrap
            endpoint: The endpoint path or name (default: auto-detected)
        """
        self.generator = generator
        self.endpoint = endpoint or self._get_caller_endpoint()
        self.start_time = time.time()

        # Track stream start
        track_stream_started(self.endpoint)

    def _get_caller_endpoint(self) -> str:
        """
        Get the endpoint name from the caller's stack frame.

        Returns:
            The endpoint name or 'unknown' if it can't be determined
        """
        try:
            # Get the caller's frame (2 levels up)
            frame = inspect.currentframe().f_back.f_back
            if frame:
                # Try to get the function name
                func_name = frame.f_code.co_name
                # Try to get the class name if it's a method
                if 'self' in frame.f_locals:
                    class_name = frame.f_locals['self'].__class__.__name__
                    return f"{class_name}.{func_name}"
                return func_name
            return "unknown"
        except Exception as e:
            logger.warning(f"Error getting caller endpoint: {e}")
            return "unknown"

    async def __aiter__(self):
        """
        Iterate through the wrapped generator, tracking metrics for each chunk.

        Yields:
            The chunks from the wrapped generator
        """
        try:
            async for chunk in self.generator:
                # Track the chunk
                chunk_size = len(chunk) if isinstance(chunk, (str, bytes)) else 1
                track_stream_chunk(self.endpoint, chunk_size)

                # Yield the chunk
                yield chunk
        except Exception as e:
            # Track the error
            error_type = type(e).__name__
            track_stream_error(self.endpoint, error_type)

            # Re-raise the exception
            logger.error(f"Error in streaming response: {e}")
            raise
        finally:
            # Track stream end
            duration = time.time() - self.start_time
            track_stream_finished(self.endpoint, duration)


def wrap_streaming_response(generator, endpoint: Optional[str] = None) -> AsyncGenerator:
    """
    Wrap a streaming generator with metrics tracking.

    This is a convenience function for creating a StreamingMetricsWrapper.

    Args:
        generator: The async generator to wrap
        endpoint: The endpoint path or name (default: auto-detected)

    Returns:
        The wrapped generator
    """
    return StreamingMetricsWrapper(generator, endpoint)


def streaming_metrics_decorator(endpoint: Optional[str] = None):
    """
    Decorator for wrapping streaming generator functions with metrics tracking.

    Args:
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

            # Wrap the generator with metrics
            return StreamingMetricsWrapper(generator, endpoint_name)

        return wrapper

    return decorator


async def track_streaming_generator(
    generator: AsyncGenerator[Any, None],
    endpoint: str
) -> AsyncGenerator[Any, None]:
    """
    Wrap a streaming generator with Prometheus metrics tracking.

    This is a simpler alternative to StreamingMetricsWrapper when you just need
    to wrap a generator directly without using a class.

    Args:
        generator: The async generator to wrap
        endpoint: The endpoint path or name

    Yields:
        The chunks from the wrapped generator
    """
    # Track stream start
    track_stream_started(endpoint)
    start_time = time.time()

    try:
        async for chunk in generator:
            # Track the chunk
            chunk_size = len(chunk) if isinstance(chunk, (str, bytes)) else 1
            track_stream_chunk(endpoint, chunk_size)

            # Yield the chunk
            yield chunk
    except Exception as e:
        # Track the error
        error_type = type(e).__name__
        track_stream_error(endpoint, error_type)

        # Re-raise the exception
        raise
    finally:
        # Track stream end
        duration = time.time() - start_time
        track_stream_finished(endpoint, duration)
