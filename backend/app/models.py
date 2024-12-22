from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

Base = declarative_base()


class Sandbox(Base):
    __tablename__ = "sandboxes"

    id = Column("id", UUID, primary_key=True, default=text("gen_random_uuid()"))
    name = Column(String, unique=True)
    status = Column(String)  # ACTIVE, TERMINATED
    created_at = Column(DateTime)  # Timestamp when the sandbox was created
    expiry_time = Column(DateTime)  # Timestamp when the sandbox will be terminated
    stack_id = Column(String)  # AWS CloudFormation stack ID
