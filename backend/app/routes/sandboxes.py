from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.aws_sandbox import create_sandbox, terminate_sandbox
from app.models import Sandbox
from app.database import get_db
from pydantic import BaseModel
from app.scheduler import schedule_task, scheduler
from app.routes.google_auth import validate_user

router = APIRouter()


class SandboxCreate(BaseModel):
    name: str


class SandboxResponse(BaseModel):
    name: str
    status: str
    created_at: datetime
    expiry_time: datetime
    stack_id: str


def terminate_sandbox_task(sandbox_name: str):
    """
    Task to terminate a sandbox environment.
    """
    print(f"Executing termination task for sandbox '{sandbox_name}'")
    from app.database import get_db  # Avoid circular imports

    db = next(get_db())

    # Fetch sandbox details
    sandbox = (
        db.query(Sandbox)
        .filter(Sandbox.name == sandbox_name, Sandbox.status == "ACTIVE")
        .first()
    )
    if sandbox:
        # Terminate the CloudFormation stack
        terminate_sandbox(sandbox.stack_id)

        # Update the database status
        sandbox.status = "TERMINATED"
        db.commit()
        print(f"Sandbox '{sandbox_name}' terminated successfully.")
    else:
        print(f"Sandbox '{sandbox_name}' not found or already terminated.")


@router.get("/", include_in_schema=True)
def read_root():
    return {"message": "Welcome to the sandbox service"}


@router.get("/test")
def get_sandboxes(user: dict = Depends(validate_user)):
    """
    Get a list of sandboxes. Protected by Google OAuth authentication.
    """
    return {"message": "Here are your sandboxes!", "user": user}


@router.post("/sandboxes", response_model=SandboxResponse)
def create_new_sandbox(
    sandbox: SandboxCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(validate_user),
):
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
        expiry_time=datetime.utcnow() + timedelta(minutes=15),
        stack_id=sandbox_response["stack_id"],
    )
    db.add(new_sandbox)
    db.commit()
    # db.refresh(new_sandbox)
    delay_minutes = 15
    schedule_task(terminate_sandbox_task, delay_minutes, sandbox.name)
    return new_sandbox


@router.get("/sandboxes")
def list_sandboxes(db: Session = Depends(get_db), user: dict = Depends(validate_user)):
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
def delete_sandbox(
    name: str, db: Session = Depends(get_db), user: dict = Depends(validate_user)
):
    """
    Terminate a sandbox environment.
    """
    sandbox = db.query(Sandbox).filter(Sandbox.name == name).first()
    if sandbox:
        terminate_sandbox(sandbox.stack_id)
        sandbox.status = "TERMINATED"
        db.commit()
    return {"message": f"Sandbox {name} terminated"}


@router.get("/jobs")
def list_jobs(user: dict = Depends(validate_user)):
    jobs = scheduler.get_jobs()
    return [{"id": job.id, "next_run_time": job.next_run_time} for job in jobs]
