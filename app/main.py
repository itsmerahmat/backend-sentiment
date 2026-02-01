import os
from contextlib import asynccontextmanager
from pathlib import Path
from sys import prefix

from fastapi import FastAPI, Request, Response
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.database import create_db_and_tables
from app.routers import users, ig_accounts, ig_posts, ig_comments, indobert_sentiment, lexicon_sentiment
from app.internal import admin

# Import all models to ensure they are registered with SQLModel
from app.models import User, InstagramAccount, InstagramPost, InstagramComment

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    create_db_and_tables()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include routers with /api prefix
app.include_router(users.router, prefix="/api")
app.include_router(ig_accounts.router, prefix="/api")
app.include_router(ig_posts.router, prefix="/api")
app.include_router(ig_comments.router, prefix="/api")
# app.include_router(admin.router, prefix="/api")
app.include_router(indobert_sentiment.router, prefix="/api")
app.include_router(lexicon_sentiment.router, prefix="/api")

# Instagram media proxy endpoint
@app.get("/instagram-proxy")
async def instagram_proxy(url: str):
    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.instagram.com/",
        }
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return Response(content="Failed to fetch image", status_code=resp.status_code)
        return Response(content=resp.content, media_type=resp.headers.get("content-type"))


@app.get("/")
async def root():
    """Root endpoint - Serve React app if available, otherwise API info."""
    index_path = STATIC_DIR / "index.html"
    if STATIC_DIR.exists() and index_path.exists():
        return FileResponse(index_path)
    
    return {
        "message": "Welcome to the API",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================
# Static Files - Serve React Build
# ============================================================
# Path ke folder build React
# For Vercel: uses 'public' directory (standard for Vercel)
# For local development: uses 'static' directory
# Contoh struktur:
#   backend/
#     public/           <- folder untuk React build (Vercel)
#       index.html
#       assets/
#       ...

STATIC_DIR = Path(__file__).parent.parent / "public"

# Cek apakah folder static ada
if STATIC_DIR.exists():
    # Mount static files (untuk assets seperti JS, CSS, images)
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # Serve file statis lainnya (favicon, manifest, dll)
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return {"detail": "Not found"}
    
    @app.get("/manifest.json")
    async def manifest():
        manifest_path = STATIC_DIR / "manifest.json"
        if manifest_path.exists():
            return FileResponse(manifest_path)
        return {"detail": "Not found"}
    
    # Catch-all route untuk SPA (Single Page Application)
    # Ini HARUS didefinisikan TERAKHIR setelah semua API routes
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """
        Serve React SPA.
        Semua route yang tidak match dengan API akan di-redirect ke index.html
        agar React Router bisa handle routing di client-side.
        """
        # Jika path dimulai dengan 'api/' atau sudah di-handle, skip
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            return {"detail": "Not found"}
        
        # Cek apakah file spesifik diminta (misal: robots.txt)
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Default: return index.html untuk SPA routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return {"detail": "React build not found. Please build your React app and copy to 'static' folder."}
