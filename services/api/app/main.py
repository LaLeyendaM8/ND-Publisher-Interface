import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response
from app.routers.projects import router as projects_router
from app.routers.health import router as health_router
from app.routers.tools import router as tools_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


app = FastAPI(
    title="ND Publisher API",
    version="0.1.0",
    description="Backend API for ND internal publisher interface.",
)

app.include_router(health_router)
app.include_router(tools_router, prefix="/tools", tags=["tools"])
app.include_router(projects_router)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
        ),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            message=detail,
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("Unhandled API exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="Unexpected server error",
        ),
    )
