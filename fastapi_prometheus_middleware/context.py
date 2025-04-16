"""
Context utilities for tracking token usage across async contexts.
"""

from contextvars import ContextVar

# Context variable to track token usage
token_usage_context: ContextVar[dict] = ContextVar(
    "token_usage_context",
    default={"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}
)
