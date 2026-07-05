"""FastAPI application factory for FDA Engine."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from fda_engine.api.routes import (
    document_router,
    verify_router,
    ws_router,
    workspace_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info("FDA Engine starting up...")
    from fda_engine.api.deps import get_state
    state = get_state()
    await state.engine.initialize()
    logger.info("FDA Engine ready")
    yield
    logger.info("FDA Engine shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FDA Medical Device Registration Automation",
        description="Automated FDA 510(k) document generation and consistency verification engine",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routes under /api/v1
    app.include_router(workspace_router, prefix="/api/v1")
    app.include_router(document_router, prefix="/api/v1")
    app.include_router(verify_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")

    # Serve static files (frontend)
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "fda-engine"}

    @app.get("/fda_frontend.html")
    async def serve_frontend():
        frontend_path = Path(__file__).parent.parent.parent / "fda_frontend.html"
        if frontend_path.exists():
            return FileResponse(str(frontend_path))
        return {"error": "Frontend not found"}

    @app.get("/")
    async def root():
        return {"message": "FDA Engine API", "docs": "/docs", "frontend": "/fda_frontend.html"}

    return app


app = create_app()
