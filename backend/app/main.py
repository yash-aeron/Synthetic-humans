import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api.experiments import router as experiments_router
from backend.app.browser.playwright_runner import browser_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure db tables and directories
    await init_db()
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    yield
    # Shutdown: gracefully close Playwright browsers
    await browser_manager.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Behavioral User-Simulation and Usability Testing Engine",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static screenshots directory
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=settings.STORAGE_DIR), name="screenshots")

# API routers
app.include_router(experiments_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Synthetic Humans Backend",
        "environment": settings.ENVIRONMENT,
        "default_provider": settings.DEFAULT_LLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
