"""
Registry for metrics instances.

This module provides a registry for metrics instances to be used across the application.
"""

import logging
from typing import Optional, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Global registry for metrics instances
_metrics_registry = {}


def register_metrics(name: str, instance: Any) -> None:
    """
    Register a metrics instance with the registry.
    
    Args:
        name: Name to register the instance under
        instance: The metrics instance to register
    """
    _metrics_registry[name] = instance


def get_metrics(name: str) -> Optional[Any]:
    """
    Get a metrics instance from the registry.
    
    Args:
        name: Name of the metrics instance to get
        
    Returns:
        The metrics instance or None if not found
    """
    return _metrics_registry.get(name)


def get_all_metrics() -> Dict[str, Any]:
    """
    Get all registered metrics instances.
    
    Returns:
        Dictionary of all registered metrics instances
    """
    return _metrics_registry.copy()
