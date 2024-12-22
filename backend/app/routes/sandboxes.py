from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.aws_sandbox import create_sandbox, terminate_sandbox
from app.models import Sandbox
from app.database import get_db
from pydantic import BaseModel

router = APIRouter()


class SandboxCreate(BaseModel):
    name: str


class SandboxResponse(BaseModel):
    name: str
    status: str
    created_at: datetime
    expiry_time: datetime
    stack_id: str


@router.post("/sandboxes", response_model=SandboxResponse)
def create_new_sandbox(sandbox: SandboxCreate, db: Session = Depends(get_db)):
    """
    Create a new sandbox
    """
    sandbox_response = create_sandbox(sandbox.name)
    if sandbox_response is None:
        raise HTTPException(status_code=500, detail="Failed to create sandbox")
    new_sandbox = Sandbox(
        name=sandbox.name,
        status=sandbox_response["status"],
        created_at=datetime.utcnow(),
        expiry_time=datetime.utcnow() + timedelta(hours=6),
        stack_id=sandbox_response["stack_id"],
    )
    db.add(new_sandbox)
    db.commit()
    db.refresh(new_sandbox)
    return new_sandbox


@router.get("/sandboxes")
def list_sandboxes(db: Session = Depends(get_db)):
    """
    List all sandboxes.
    """
    sandboxes = db.query(Sandbox).all()
    return [
        {
            "name": sandbox.name,
            "status": sandbox.status,
            "expiry_time": sandbox.expiry_time,
        }
        for sandbox in sandboxes
    ]


@router.delete("/sandboxes/{name}")
def delete_sandbox(name: str, db: Session = Depends(get_db)):
    """
    Terminate a sandbox environment.
    """
    sandbox = db.query(Sandbox).filter(Sandbox.name == name).first()
    if sandbox:
        terminate_sandbox(sandbox.stack_id)
        sandbox.status = "TERMINATED"
        db.commit()
    return {"message": f"Sandbox {name} terminated"}
