from fastapi import FastAPI
from app.routes import sandboxes
from app.models import Base
from app.database import engine
from app.scheduler import scheduler

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(sandboxes.router, prefix="/api", tags=["Sandboxes"])


# Start the scheduler if it's not already running
if not scheduler.running:
    scheduler.start()


@app.on_event("startup")
async def startup_event():
    # Additional startup tasks can be added here
    pass


@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown the scheduler
    if scheduler.running:
        scheduler.shutdown()
