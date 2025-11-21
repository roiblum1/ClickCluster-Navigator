"""
Main FastAPI application for OpenShift Cluster Navigator.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager
from src.api import clusters_router, sites_router, vlan_sync_router, combined_router, statistics_router, export_router
from src.services import vlan_sync_service
from src.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Start VLAN sync service
    await vlan_sync_service.start()
    # Perform initial sync
    await vlan_sync_service.sync_data()
    yield
    # Shutdown: Stop VLAN sync service
    vlan_sync_service.stop()

# Create FastAPI app
app = FastAPI(
    title="OpenShift Cluster Navigator",
    description="API for managing and navigating OpenShift clusters organized by site",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clusters_router)
app.include_router(sites_router)
app.include_router(vlan_sync_router)
app.include_router(combined_router)
app.include_router(statistics_router)
app.include_router(export_router)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_title": config.app_title
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "openshift-cluster-navigator"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
