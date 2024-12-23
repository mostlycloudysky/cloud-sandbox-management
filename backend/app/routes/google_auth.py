from fastapi import APIRouter, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import os

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
)


