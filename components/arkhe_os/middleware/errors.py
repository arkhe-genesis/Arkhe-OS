from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from arkhe_os.middleware.logging import logger

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        path=request.url.path,
        exception_type=type(exc).__name__
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "type": type(exc).__name__},
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
