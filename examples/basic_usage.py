"""
Basic usage example for FastAPI Prometheus Middleware.
"""

import asyncio
from fastapi import FastAPI
from fastapi_prometheus_middleware import PrometheusMiddleware, metrics_endpoint, generate_prometheus_data

app = FastAPI()

# Add the Prometheus middleware
app.add_middleware(
    PrometheusMiddleware,
    prefix="example",  # Custom prefix for metrics
    skip_paths=["/metrics", "/health"],  # Paths to skip tracking
)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)

# Write metrics to a file every 10 seconds
async def write_metrics_to_file():
    while True:
        await generate_prometheus_data("metrics.prom")
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(write_metrics_to_file())

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
