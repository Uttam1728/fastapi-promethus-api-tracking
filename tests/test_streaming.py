"""
Tests for the streaming response functionality of the FastAPI Prometheus Middleware.
"""

import pytest
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse
from fastapi_prometheus_middleware import (
    PrometheusMiddleware, 
    metrics_endpoint,
    wrap_streaming_response,
    streaming_response_decorator
)


@pytest.fixture
def app():
    """Create a FastAPI app with the Prometheus middleware."""
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware, prefix="test")
    app.add_route('/metrics', metrics_endpoint)
    
    @app.get("/stream")
    async def stream_data():
        async def generator():
            for i in range(3):
                yield f"data: {i}\n\n"
        
        # Wrap the generator with metrics tracking
        tracked_generator = wrap_streaming_response(generator(), endpoint="/stream")
        
        return StreamingResponse(tracked_generator, media_type="text/event-stream")
    
    @app.get("/stream2")
    @streaming_response_decorator(media_type="text/event-stream")
    async def stream_data2():
        for i in range(3):
            yield f"data: {i}\n\n"
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_wrapped_streaming_response(client):
    """Test that wrapped streaming responses work."""
    response = client.get("/stream")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Get the metrics
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    
    # Check that the streaming metrics contain the expected data
    metrics_text = metrics_response.text
    assert "test_stream_chunks_total" in metrics_text
    assert "test_stream_bytes_total" in metrics_text


def test_decorated_streaming_response(client):
    """Test that decorated streaming responses work."""
    response = client.get("/stream2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Get the metrics
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    
    # Check that the streaming metrics contain the expected data
    metrics_text = metrics_response.text
    assert "test_stream_chunks_total" in metrics_text
    assert "test_stream_bytes_total" in metrics_text
