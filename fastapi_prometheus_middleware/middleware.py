"""
Prometheus middleware for FastAPI applications.

This module provides a middleware that tracks request metrics using Prometheus.
"""
from datetime import datetime
import time
import typing
from typing import Callable, List, Optional, Dict, Any

from pydantic import BaseModel, Field

try:
    import orjson
except ImportError:
    import json as orjson
    orjson.loads = orjson.loads
    orjson.dumps = lambda obj, **kwargs: orjson.dumps(obj).encode('utf-8')

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import StreamingResponse

from fastapi_prometheus_middleware.context import token_usage_context
from fastapi_prometheus_middleware.metrics import (
    track_request_started,
    track_request_completed,
    track_request_error,
    track_request_finished,
    track_token_usage
)
from fastapi_prometheus_middleware.exception_tracker import track_detailed_exception

class UserData(BaseModel):
    userId: int = Field(..., alias="_id")
    orgId: typing.Optional[int] = None
    firstName: typing.Optional[str]
    lastName: typing.Optional[str]
    email: typing.Optional[str]
    username: typing.Optional[str]
    phoneNumber: typing.Optional[str]
    profilePicUrl: typing.Optional[str]
    active: typing.Optional[bool]
    roleIds: typing.Optional[list[int]]
    meta: typing.Optional[dict]
    createdAt: typing.Optional[datetime]
    updatedAt: typing.Optional[datetime]
    workspace: typing.List[typing.Dict]


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking FastAPI request metrics with Prometheus.
    
    This middleware tracks:
    - Request counts
    - Request durations
    - Request sizes
    - Response sizes
    - Errors
    - Token usage (for LLM applications)
    
    It also provides detailed logging of requests and responses.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        prefix: str = "fastapi",
        skip_paths: Optional[List[str]] = None,
        logger: Any = None,
        **kwargs
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            prefix: Prefix for Prometheus metrics (default: "fastapi")
            skip_paths: List of paths to skip tracking (default: ["/metrics", "/_readyz", "/_healthz"])
            logger: Logger instance to use for logging (default: None)
            **kwargs: Additional arguments to pass to the parent class
        """
        super().__init__(app)
        self.prefix = prefix
        self.skip_paths = skip_paths or ["/metrics", "/_readyz", "/_healthz"]
        self.logger = logger

    async def process_request_data(self, request: Request) -> Dict[str, Any]:
        """
        Process and extract data from the request.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            A dictionary containing request data
        """
        request_data = {
            'client_host': request.client,
            'url': request.url.components,
            'url_path': request.url.path,
            'request_method': request.method,
            'path_params': dict(request.path_params.items()),
            'query_params': dict(request.query_params.items()),
            'headers': dict(request.headers.items()),
            'request_body': await request.body()
        }
        return request_data

    def process_request_headers(self, request: Request, request_data: Dict[str, Any]) -> None:
        """
        Process request headers and update request data.
        
        Args:
            request: The FastAPI request object
            request_data: The request data dictionary to update
        """
        content_type = request.headers.get("content-type", "")
        try:
            request_data['request_body'] = (
                orjson.loads(request_data['request_body'])
                if request_data['request_body'] and not content_type.startswith("multipart/form-data")
                else {}
            )
            if x_user_data := request.headers.get("x-user-data"):
                request.state.user_data = UserData.construct(**orjson.loads(x_user_data))

        except (ValueError, TypeError):
            request_data['request_body'] = {}

    def process_response(self, request: Request, response: Response, request_data: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """
        Process the response and extract data.
        
        Args:
            request: The FastAPI request object
            response: The response object
            request_data: The request data dictionary
            start_time: The start time of the request
            
        Returns:
            A dictionary containing response data
        """
        end_time = time.perf_counter()
        request_data['request_duration'] = end_time - start_time

        if isinstance(response, StreamingResponse):
            return {
                'status_code': response.status_code, 
                'body': {
                    'data': 'streaming response'
                }
            }
        elif hasattr(response, 'template'):
            return {
                'status_code': response.status_code,
                'body': {'template': 'template response'}
            }
        else:
            try:
                body = response.body.decode('utf-8') if hasattr(response, 'body') and response.body else ''
                return {
                    'status_code': response.status_code,
                    'body': orjson.loads(body) if body else ''
                }
            except (AttributeError, ValueError, TypeError):
                return {
                    'status_code': response.status_code,
                    'body': str(response)
                }

    def log_request(self, level: str, request_data: Dict[str, Any], response_data: Dict[str, Any], request_time: float) -> None:
        """
        Log request and response data.
        
        Args:
            level: Log level ("info" or "error")
            request_data: The request data dictionary
            response_data: The response data dictionary
            request_time: The request duration in seconds
        """
        if not self.logger:
            return
            
        log_data = {
            "status": response_data.get('status_code', 200),
            'apiTime': request_time,
            'request': request_data,
            'response': response_data
        }
        
        if level == "info":
            self.logger.info(log_data)
        else:
            self.logger.error(log_data)

    async def handle_exception(self, request: Request, request_data: Dict[str, Any], exc: Exception, status_code: int, start_time: float) -> Response:
        """
        Handle exceptions that occur during request processing.
        
        Args:
            request: The FastAPI request object
            request_data: The request data dictionary
            exc: The exception that occurred
            status_code: The HTTP status code to return
            start_time: The start time of the request
            
        Returns:
            A response object
        """
        from fastapi.responses import JSONResponse
        
        request_data["error"] = [str(exc)] if not isinstance(exc, list) else exc
        end_time = time.perf_counter()
        request_data['request_duration'] = end_time - start_time
        
        if self.logger:
            self.logger.exception(
                f"Exception occurred for {request_data['url_path']}", 
                extra={'request_data': request_data}
            )
        
        error_response = {"errors": request_data["error"], "success": False}
        response_obj = {
            'status_code': status_code,
            "error_response": error_response
        }
        
        self.log_request("error", request_data, response_obj, end_time - start_time)
        return JSONResponse(content=error_response, status_code=status_code)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and track metrics.
        
        Args:
            request: The FastAPI request object
            call_next: The next middleware or endpoint to call
            
        Returns:
            The response from the next middleware or endpoint
        """
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Initialize token usage context
        token_usage_context.set({"total_tokens": 0, "input_tokens": 0, "output_tokens": 0})
        start_time = time.perf_counter()

        # Process request data
        request_data = await self.process_request_data(request)
        
        # Track request start
        request_body_size = len(request_data.get('request_body', b''))
        track_request_started(request, request_body_size)

        try:
            self.process_request_headers(request, request_data)
            response = await call_next(request)
            response_data = self.process_response(request, response, request_data, start_time)
            self.log_request("info", request_data, response_data, time.perf_counter() - start_time)

            # Track successful completion
            duration = time.perf_counter() - start_time
            track_request_completed(request, response, duration)
            
            return response

        except Exception as exc:
            duration = time.perf_counter() - start_time
            status_code = getattr(exc, 'status_code', 500)
            track_request_error(request, status_code, type(exc).__name__, duration)
            track_detailed_exception(exc, status_code)
            return await self.handle_exception(request, request_data, exc, status_code, start_time)

        finally:
            track_request_finished(request)

            # Track token usage
            token_data = token_usage_context.get()
            if token_data["total_tokens"] > 0:
                track_token_usage(
                    input_tokens=token_data["input_tokens"],
                    output_tokens=token_data["output_tokens"],
                    total_tokens=token_data["total_tokens"]
                )

            # Reset token usage context
            token_usage_context.set({"total_tokens": 0, "input_tokens": 0, "output_tokens": 0})
