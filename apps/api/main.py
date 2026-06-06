"""OpenCord FastAPI Application Entry"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import init_db
from api import auth, users, channels, posts, comments, ai, admin, export, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="OpenCord API",
    version=settings.OPENCORD_VERSION,
    description="OpenCord / 开弦 — An open, AI-native community system.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "version": settings.OPENCORD_VERSION}


# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
