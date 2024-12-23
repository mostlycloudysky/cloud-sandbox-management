from fastapi import APIRouter, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "email profile"},
)


@router.get("/login")
async def login(request: Request):
    redirect_uri = "http://localhost:8000/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request):
    try:
        logger.info("Callback query parameters: %s", request.query_params)

        # Exchange authorization code for token
        token = await oauth.google.authorize_access_token(request)
        logger.info("Token received: %s", token)

        # Fetch user info from the userinfo endpoint
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        response = requests.get(userinfo_endpoint, headers=headers)
        response.raise_for_status()
        user = response.json()

        logger.info("User info received: %s", user)

    except Exception as e:
        logger.error("Authentication failed: %s", str(e))
        raise HTTPException(status_code=400, detail="Authentication failed")

    return {
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
    }


async def validate_user(request: Request):
    """
    Validate the access token and fetch user info from Google's userinfo endpoint.
    """
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        logger.error("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    token = token.split(" ")[1]  # Extract the access token
    logger.info("Access token received: %s", token)

    try:
        # Fetch user info from the userinfo endpoint
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(userinfo_endpoint, headers=headers)
        response.raise_for_status()

        # Parse and return user info
        user = response.json()
        logger.info("User info retrieved: %s", user)
        return user
    except Exception as e:
        logger.error("Token validation failed: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")
