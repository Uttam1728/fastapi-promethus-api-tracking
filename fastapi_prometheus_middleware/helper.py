"""
Helper functions for Prometheus metrics.

This module provides utility functions for working with Prometheus metrics.
"""

import logging
import os
from typing import Optional

from prometheus_client import generate_latest, REGISTRY

# Set up logging
logger = logging.getLogger(__name__)


async def generate_prometheus_data(file_path: Optional[str] = None):
    """
    Generate Prometheus metrics data and write it to a file.
    
    Args:
        file_path: Path to the file to write the metrics to (default: None)
            If None, the function will return the metrics data as a string.
            
    Returns:
        The metrics data as a string if file_path is None, otherwise None.
    """
    data = generate_latest(registry=REGISTRY).decode('utf-8', errors='ignore')
    
    if file_path:
        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                file.write(data)
        except Exception as e:
            logger.error(f"Error writing Prometheus data to file: {e}")
    else:
        return data
