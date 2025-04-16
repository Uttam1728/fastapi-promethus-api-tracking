"""
Tests for the FastAPI Prometheus Middleware.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint


@pytest.fixture
def app():
    """Create a FastAPI app with the Prometheus middleware."""
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware, prefix="test")
    app.add_route('/metrics', metrics_endpoint)
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    @app.get("/items/{item_id}")
    async def read_item(item_id: int):
        return {"item_id": item_id}
    
    @app.get("/error")
    async def error():
        raise ValueError("Test error")
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test that the root endpoint works."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_items_endpoint(client):
    """Test that the items endpoint works."""
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1}


def test_metrics_endpoint(client):
    """Test that the metrics endpoint works."""
    # Make some requests to generate metrics
    client.get("/")
    client.get("/items/1")
    
    # Get the metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check that the metrics contain the expected data
    metrics_text = response.text
    assert "test_http_requests_total" in metrics_text
    assert "test_http_request_duration_seconds" in metrics_text


def test_error_tracking(client):
    """Test that errors are tracked."""
    # Make a request that will cause an error
    response = client.get("/error", expect_errors=True)
    assert response.status_code == 500
    
    # Get the metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check that the error metrics contain the expected data
    metrics_text = response.text
    assert "test_errors_total" in metrics_text
    assert "test_exceptions_total" in metrics_text
