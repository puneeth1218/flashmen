"""
FastAPI Router Package.
Includes endpoints for ingestion, alerts, dashboard stats, network graph, and global search.
"""
from .ingest import router as ingest_router
from .alerts import router as alerts_router
from .stats import router as stats_router
from .graph import router as graph_router
from .search import router as search_router

__all__ = ["ingest_router", "alerts_router", "stats_router", "graph_router", "search_router"]
