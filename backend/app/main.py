from fastapi import FastAPI
from app.routes import sandboxes
from app.models import Base
from app.database import engine
from app.scheduler import scheduler
from app.routes.google_auth import router as google_auth_router
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add middleware
app.add_middleware(
    SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "your_secret_key")
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(sandboxes.router, prefix="/api", tags=["Sandboxes"])
app.include_router(google_auth_router, prefix="/auth", tags=["Google Auth"])


@app.on_event("startup")
async def startup_event():
    # Start the scheduler if it's not already running
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown the scheduler
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")
