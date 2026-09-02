"""
FastAPI Main Application Entrypoint.
Configures CORS middleware, lifespan context handlers, and mounts API routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import (
    ingest_router,
    alerts_router,
    stats_router,
    graph_router,
    search_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager handling startup initialization and shutdown cleanup.
    """
    print("🚀 Starting Bitcoin Traffic Monitor API Services...")
    # Add startup initialization (e.g. database schema creation, loading GeoLite2 DB)
    yield
    print("🛑 Shutting down Bitcoin Traffic Monitor API Services...")


app = FastAPI(
    title="Bitcoin Traffic Monitor API",
    description="Backend API for Bitcoin network traffic monitoring, anomaly detection, and graph analytics.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(ingest_router)
app.include_router(alerts_router)
app.include_router(stats_router)
app.include_router(graph_router)
app.include_router(search_router)


@app.get("/", tags=["Health"])
async def root_health_check():
    """
    Root health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "Bitcoin Traffic Monitor API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
