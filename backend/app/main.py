from fastapi import FastAPI
from app.routes import sandboxes
from app.models import Base
from app.database import engine

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(sandboxes.router, prefix="/api", tags=["Sandboxes"])
