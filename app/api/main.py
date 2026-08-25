"""
FastAPI Application Entrypoint
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.core.security import AuthManager
from app.api.routes import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Cau360 Market Intelligence System for Vietnam & China Areca Nut Trade"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Core Database & Auth Tables
    init_db()
    AuthManager.init_auth_table()
    
    # Include REST API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Mount Frontend Static Directory for PWA
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")
        
    @app.get("/")
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "RUNNING",
            "api_docs": "/docs",
            "pwa_app": "/app"
        }
        
    return app

app = create_app()
