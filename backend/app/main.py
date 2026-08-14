"""
LLM Security Assessment Platform – Backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import logging

from app.core.config import settings
from app.core.database import init_db
from app.routers import health, scans, results, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lsap")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LSAP backend…")
    await init_db()
    yield
    logger.info("Shutting down LSAP backend…")


app = FastAPI(
    title="LLM Security Assessment Platform",
    description="Unified API for multi-tool LLM red-teaming and vulnerability assessment",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(results.router, prefix="/api/v1/results", tags=["Results"])


@app.get("/")
async def root():
    return {
        "service": "LLM Security Assessment Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "ok",
    }
