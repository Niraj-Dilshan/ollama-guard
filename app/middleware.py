import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    """
    Log incoming requests and outgoing responses.
    """
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"Request: {request.method} {request.url.path} - Response: {response.status_code} - Process Time: {process_time:.2f}ms"
    )
    
    return response
