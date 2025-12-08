"""
Logging middleware for FastAPI application.
"""
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Log incoming request
        logger.info(f"→ {method} {path} from {client_host}")

        # Process request
        try:
            response: Response = await call_next(request)

            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to ms

            # Log response
            status_code = response.status_code
            if status_code < 400:
                logger.info(f"← {method} {path} {status_code} ({duration:.2f}ms)")
            elif status_code < 500:
                logger.warning(f"← {method} {path} {status_code} ({duration:.2f}ms)")
            else:
                logger.error(f"← {method} {path} {status_code} ({duration:.2f}ms)")

            # Add custom headers
            response.headers["X-Process-Time"] = f"{duration:.2f}ms"

            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"← {method} {path} ERROR ({duration:.2f}ms): {str(e)}")
            raise


class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    """
    More detailed logging middleware that includes request body and query params.
    Use this for debugging only, as it may log sensitive data.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Process the request with detailed logging.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        start_time = time.time()

        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"

        # Log request details
        logger.debug(f"Request Details:")
        logger.debug(f"  Method: {method}")
        logger.debug(f"  Path: {path}")
        logger.debug(f"  Client: {client_host}")
        logger.debug(f"  Query Params: {query_params}")
        logger.debug(f"  Headers: {dict(request.headers)}")

        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000

            logger.debug(f"Response Details:")
            logger.debug(f"  Status: {response.status_code}")
            logger.debug(f"  Duration: {duration:.2f}ms")

            response.headers["X-Process-Time"] = f"{duration:.2f}ms"

            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Request failed after {duration:.2f}ms: {str(e)}", exc_info=True)
            raise
