from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api import auth, tickets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and pgvector extension on startup
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Cuort: AI-Powered Customer Support Orchestrator API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["Tickets"])

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} AI API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
