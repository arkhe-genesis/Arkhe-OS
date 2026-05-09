import logging
import json
import time
from fastapi import Request
from pythonjsonlogger import jsonlogger

class ArkheLogger:
    def __init__(self, name="arkhe_os"):
        self.logger = logging.getLogger(name)
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(levelname)s %(name)s %(message)s %(coherence_M)s'
        )
        logHandler.setFormatter(formatter)
        self.logger.addHandler(logHandler)
        self.logger.setLevel(logging.INFO)

    def info(self, msg, **kwargs):
        kwargs.setdefault('timestamp', time.time())
        self.logger.info(msg, extra=kwargs)

    def error(self, msg, **kwargs):
        kwargs.setdefault('timestamp', time.time())
        self.logger.error(msg, extra=kwargs)

logger = ArkheLogger()

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Try to get coherence from state if available
    coherence_M = getattr(request.app.state, 'scaffold', None)
    m_val = coherence_M.coherence_M if coherence_M else 1.0

    logger.info(
        f"Request: {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
        coherence_M=m_val
    )
    return response
