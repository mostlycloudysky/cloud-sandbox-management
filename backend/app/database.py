import boto3
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
hostname = os.getenv("DB_HOSTNAME")
if not hostname:
    raise ValueError("DB_HOSTNAME environment variable is not set")
region = "us-east-1"
client = boto3.client("dsql", region_name=region)
password_token = client.generate_db_connect_admin_auth_token(hostname, region)
url = URL.create(
    "postgresql+psycopg2",
    username="admin",
    password=password_token,
    host=hostname,
    database="postgres",
)

engine = create_engine(url, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
