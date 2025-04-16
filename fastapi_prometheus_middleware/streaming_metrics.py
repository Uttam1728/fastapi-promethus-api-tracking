"""
Prometheus metrics for streaming responses.

This module defines metrics and utilities for tracking streaming response performance.
"""

import time
import logging
import inspect
from typing import AsyncGenerator, Any, Optional, Callable, Dict, List, Union

from prometheus_client import Counter, Histogram, Gauge, REGISTRY
from fastapi import Request

# Set up logging
logger = logging.getLogger(__name__)


class StreamingMetrics:
    """
    Class for tracking streaming response metrics using Prometheus.
    
    This class provides methods for tracking various aspects of streaming responses,
    including active streams, chunk counts, bytes sent, duration, and errors.
    """
    
    def __init__(self, prefix: str = 'fastapi'):
        """
        Initialize the streaming metrics with the given prefix.
        
        Args:
            prefix: Prefix for all metric names (default: 'fastapi')
        """
        self.prefix = prefix
        
        # Define Prometheus metrics with safe creation to avoid duplicates
        self.active_streams = self._create_or_get_gauge(
            f'{prefix}_active_streams',
            'Number of active streaming responses',
            ['endpoint']
        )
        
        self.stream_chunks_total = self._create_or_get_counter(
            f'{prefix}_stream_chunks_total',
            'Total number of chunks sent in streaming responses',
            ['endpoint']
        )
        
        self.stream_bytes_total = self._create_or_get_counter(
            f'{prefix}_stream_bytes_total',
            'Total bytes sent in streaming responses',
            ['endpoint']
        )
        
        self.stream_duration_seconds = self._create_or_get_histogram(
            f'{prefix}_stream_duration_seconds',
            'Duration of streaming responses in seconds',
            ['endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
        )
        
        self.stream_errors_total = self._create_or_get_counter(
            f'{prefix}_stream_errors_total',
            'Total number of errors in streaming responses',
            ['endpoint', 'error_type']
        )
    
    def _create_or_get_counter(self, name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Counter:
        """
        Create a new Counter or return an existing one with the same name.
        
        Args:
            name: Metric name
            documentation: Metric documentation
            labelnames: List of label names
            
        Returns:
            A Counter metric
        """
        try:
            # Try to create a new Counter
            return Counter(name, documentation, labelnames or [])
        except ValueError:
            # If it already exists, try to get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a different name
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
            A Histogram metric
        """
        try:
            # Try to create a new Histogram
            return Histogram(name, documentation, labelnames or [], buckets=buckets)
        except ValueError:
            # If it already exists, try to get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a different name
            return Histogram(f"{name}_new", documentation, labelnames or [], buckets=buckets)
    
    def _create_or_get_gauge(self, name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Gauge:
        """
        Create a new Gauge or return an existing one with the same name.
        
        Args:
            name: Metric name
            documentation: Metric documentation
            labelnames: List of label names
            
        Returns:
            A Gauge metric
        """
        try:
            # Try to create a new Gauge
            return Gauge(name, documentation, labelnames or [])
        except ValueError:
            # If it already exists, try to get it from the registry
            for metric in REGISTRY._names_to_collectors.values():
                if metric.name == name:
                    return metric
            # If we can't find it, create a new one with a different name
            return Gauge(f"{name}_new", documentation, labelnames or [])
    
    def _safe_labels(self, metric: Any, labels_dict: Dict[str, str]) -> Any:
        """
        Safely get a labeled metric, handling any exceptions.
        
        Args:
            metric: The metric object
            labels_dict: Dictionary of label names and values
            
        Returns:
            The labeled metric or None if an error occurred
        """
        try:
            return metric.labels(**labels_dict)
        except Exception as e:
            logger.warning(f"Error getting labels for metric: {e}")
            return None
    
    def track_stream_started(self, endpoint: str) -> None:
        """
        Track the start of a streaming response.
        
        Args:
            endpoint: The endpoint path or name
        """
        try:
            labeled_metric = self._safe_labels(self.active_streams, {"endpoint": endpoint})
            if labeled_metric:
                labeled_metric.inc()
        except Exception as e:
            logger.warning(f"Error tracking stream start: {e}")
    
    def track_stream_chunk(self, endpoint: str, chunk_size: int) -> None:
        """
        Track a chunk sent in a streaming response.
        
        Args:
            endpoint: The endpoint path or name
            chunk_size: Size of the chunk in bytes
        """
        try:
            # Track chunk count
            labeled_metric = self._safe_labels(self.stream_chunks_total, {"endpoint": endpoint})
            if labeled_metric:
                labeled_metric.inc()
            
            # Track bytes sent
            labeled_metric = self._safe_labels(self.stream_bytes_total, {"endpoint": endpoint})
            if labeled_metric:
                labeled_metric.inc(chunk_size)
        except Exception as e:
            logger.warning(f"Error tracking stream chunk: {e}")
    
    def track_stream_finished(self, endpoint: str, duration: float) -> None:
        """
        Track the end of a streaming response.
        
        Args:
            endpoint: The endpoint path or name
            duration: Duration of the stream in seconds
        """
        try:
            # Decrement active streams
            labeled_metric = self._safe_labels(self.active_streams, {"endpoint": endpoint})
            if labeled_metric:
                labeled_metric.dec()
            
            # Record duration
            labeled_metric = self._safe_labels(self.stream_duration_seconds, {"endpoint": endpoint})
            if labeled_metric:
                labeled_metric.observe(duration)
        except Exception as e:
            logger.warning(f"Error tracking stream finish: {e}")
    
    def track_stream_error(self, endpoint: str, error_type: str) -> None:
        """
        Track an error in a streaming response.
        
        Args:
            endpoint: The endpoint path or name
            error_type: Type of error that occurred
        """
        try:
            labeled_metric = self._safe_labels(self.stream_errors_total, {
                "endpoint": endpoint,
                "error_type": error_type
            })
            if labeled_metric:
                labeled_metric.inc()
        except Exception as e:
            logger.warning(f"Error tracking stream error: {e}")

