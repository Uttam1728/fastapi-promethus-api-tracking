"""
Example showing how to use the fastapi-prometheus-middleware package in the Cerebrum project.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Import from the new package
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint, generate_prometheus_data

# Constants
PROMETHEUS_LOG_TIME = 10

async def repeated_task_for_prometheus():
    """
    Periodically write Prometheus metrics to a file.
    """
    while True:
        # Get the log file path from config
        log_file = "logs.prom"
        if os.getenv("METRICS_DIR"):
            log_file = f'{os.getenv("METRICS_DIR")}/app.prom'

        await generate_prometheus_data(log_file)
        await asyncio.sleep(PROMETHEUS_LOG_TIME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler.
    """
    # Run startup tasks
    asyncio.create_task(repeated_task_for_prometheus())
    yield
    # Run shutdown tasks


def get_app() -> FastAPI:
    """
    Get FastAPI application with Prometheus middleware.
    """
    app = FastAPI(
        title="My App",
        lifespan=lifespan,
    )

    # Add the Prometheus middleware with a custom prefix
    import logging
    logger = logging.getLogger(__name__)
    
    app.add_middleware(
        PrometheusMiddleware,
        prefix="myapp",
        logger=logger
    )

    # Add the metrics endpoint
    app.add_route('/metrics', metrics_endpoint)
    
    return app


# Example usage
if __name__ == "__main__":
    import uvicorn
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
