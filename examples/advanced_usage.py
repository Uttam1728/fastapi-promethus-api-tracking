"""
Advanced usage example for FastAPI Prometheus Middleware.
"""

import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi_prometheus_middleware import (
    PrometheusMiddleware, 
    metrics_endpoint,
    track_detailed_exception,
    track_global_exception,
    wrap_streaming_response,
    streaming_response_decorator
)
from fastapi_prometheus_middleware.context import token_usage_context

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add the Prometheus middleware with custom configuration
app.add_middleware(
    PrometheusMiddleware,
    prefix="advanced",  # Custom prefix for metrics
    skip_paths=["/metrics", "/health"],  # Paths to skip tracking
    logger=logger  # Custom logger
)

# Add the metrics endpoint
app.add_route('/metrics', metrics_endpoint)

# Write metrics to a file every 10 seconds
async def write_metrics_to_file():
    while True:
        from fastapi_prometheus_middleware import generate_prometheus_data
        await generate_prometheus_data("advanced_metrics.prom")
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(write_metrics_to_file())

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Track token usage in your LLM application
@app.post("/generate")
async def generate_text(prompt: str):
    # Simulate LLM processing
    await asyncio.sleep(0.5)
    
    # Track token usage
    token_data = token_usage_context.get()
    token_data["input_tokens"] = len(prompt.split())  # Simple token count
    token_data["output_tokens"] = 20  # Simulated output tokens
    token_data["total_tokens"] = token_data["input_tokens"] + token_data["output_tokens"]
    token_usage_context.set(token_data)
    
    return {"text": f"Generated text based on: {prompt}"}

# Track exceptions
@app.get("/risky")
async def risky_operation():
    try:
        # Some risky operation
        result = 1 / 0
    except Exception as e:
        # Track the exception
        track_detailed_exception(e, 500)
        return {"error": "An error occurred"}

# Option 1: Wrap an existing generator
@app.get("/stream")
async def stream_data():
    async def generator():
        for i in range(10):
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.1)
    
    # Wrap the generator with metrics tracking
    tracked_generator = wrap_streaming_response(generator(), endpoint="/stream")
    
    return StreamingResponse(tracked_generator, media_type="text/event-stream")

# Option 2: Use the decorator
@app.get("/stream2")
@streaming_response_decorator(media_type="text/event-stream")
async def stream_data2():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(0.1)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Process the request
    response = await call_next(request)
    
    # Log the request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
