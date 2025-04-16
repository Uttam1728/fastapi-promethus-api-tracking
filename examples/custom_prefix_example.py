"""
Example showing how to use the middleware with a custom prefix.

This example demonstrates how to properly set up the middleware with a custom prefix
to ensure all metrics are properly prefixed.
"""

import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_prometheus_middleware import (
    PrometheusMiddleware,
    metrics_endpoint,
    wrap_streaming_response,
    track_detailed_exception
)
from starlette.responses import StreamingResponse

app = FastAPI()

# Add the Prometheus middleware with a custom prefix
app.add_middleware(
    PrometheusMiddleware,
    prefix="custom_app",  # This prefix will be used for all metrics
    skip_paths=["/metrics", "/health"],
)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)

# Regular endpoint
@app.get("/hello")
async def hello():
    return {"message": "Hello World"}

# Streaming endpoint
@app.get("/stream")
async def stream_data():
    async def generator():
        for i in range(5):
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.1)

    # Wrap the generator with metrics tracking
    tracked_generator = wrap_streaming_response(generator(), endpoint="/stream")

    return StreamingResponse(tracked_generator, media_type="text/event-stream")

# Error endpoint
@app.get("/error")
async def error():
    try:
        # Some code that might raise an exception
        result = 1 / 0
    except Exception as e:
        # Track the exception
        track_detailed_exception(e, 500)
        return {"error": "This is a test error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
