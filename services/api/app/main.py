from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.tools import router as tools_router


app = FastAPI(
    title="ND Publisher API",
    version="0.1.0",
    description="Backend API for ND internal publisher interface.",
)

app.include_router(health_router)
app.include_router(tools_router, prefix="/tools", tags=["tools"])
