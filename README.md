# cloud-sandbox-management

## Overview

This project implements a **Cloud Sandbox Management tool** using:

Here are the details on the backend implementation and watch out this repo for a full frontend integration as well. 

- **FastAPI**: A modern Python web framework for building APIs.
- **Amazon Aurora DSQL(Preview)**: Used as the backend database.
- **OAuth2 with Google**: Secures API endpoints and provides authentication.
- **AWS ECS (Elastic Container Service)**: Deploys the application in a scalable and reliable manner.

The API allows users to:
- Create and manage cloud sandbox environments.
- Schedule automatic termination of sandboxes.
- List and delete sandboxes.
- Secure sensitive endpoints using Google OAuth2.

---

## Features

- **Authentication**:
  - Google OAuth2 integration to secure API endpoints.
  - Protected routes using `Depends(validate_user)`.

- **Database Integration**:
  - Amazon Aurora DSQL(Preview) is used to store sandbox data.
  - SQLAlchemy ORM for database interactions.

- **Sandbox Management**:
  - Create, list, and delete sandboxes.
  - Automatically terminate sandboxes after a set duration using `APScheduler`.

- **Scalability**:
  - Deployed on AWS ECS with Dockerized containers.

---

## Project Structure

```
cloud-sandbox-management/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── sandboxes.py         # Sandbox management routes
│   │   │   ├── google_auth.py       # OAuth2 integration with Google
│   │   ├── models.py                # SQLAlchemy models for the database
│   │   ├── database.py              # Database connection setup
│   │   ├── scheduler.py             # APScheduler integration for task scheduling
│   ├── Dockerfile                   # Dockerfile for backend container
│   ├── requirements.txt             # Python dependencies
├── README.md                        # Project documentation
├── iac/                             # Terraform files for ECS and Aurora setup
└── .gitignore                       # Git ignore rules
```

---

## Prerequisites

- **Python**: Version 3.10 or higher.
- **AWS Account**: With access to ECS, Aurora DSQL, and related services.
- **Google Cloud Console**:
  - OAuth2 credentials for API authentication.

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/cloud-sandbox-management.git
cd cloud-sandbox-management
```

### 2. Backend Setup

#### a. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # For Windows: .venv\Scripts\activate
```

#### b. Install Dependencies
```bash
pip install -r requirements.txt
```

#### c. Configure Environment Variables
Create a `.env` file in the `backend` directory:
```env
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<aurora-endpoint>:5432/<database>
SESSION_SECRET_KEY=<your-random-session-key>
```

#### d. Run the Backend Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access the API at `http://localhost:8000`.

---

### 3. Database Setup (Aurora PostgreSQL)

1. Create an Aurora DSQL instance in your AWS account.
2. Update the `DATABASE_URL` in the `.env` file with your Aurora instance details.
3. Apply migrations to initialize the database:
   ```bash
   python -m app.models
   ```

---

### 4. Authentication Setup

#### a. Create OAuth2 Credentials
1. Go to **Google Cloud Console** → **APIs & Services** → **Credentials**.
2. Create an **OAuth 2.0 Client ID**.
3. Add the redirect URI: `http://localhost:8000/auth/callback`.
4. Copy the **Client ID** and **Client Secret** to your `.env` file.

#### b. Test Authentication Locally
1. Navigate to `http://localhost:8000/auth/login` in your browser.
2. Log in with your Google account.
3. Ensure the callback route (`/auth/callback`) processes the login successfully.

---

### 5. Deploy to AWS ECS

#### a. Build and Push Docker Image
```bash
docker build -t <ecr-repository-url>:latest .
docker push <ecr-repository-url>:latest
```

#### b. Terraform Deployment
1. Navigate to the `terraform/` directory.
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Apply the configuration:
   ```bash
   terraform apply
   ```
4. Confirm the ECS service is running and connected to the Aurora database.

---

## API Endpoints

### Open Endpoints
- `GET /api/`: Welcome message (no authentication required).

### Protected Endpoints (Require OAuth2 Token)
- `GET /api/test`: Get sandbox information.
- `POST /api/sandboxes`: Create a new sandbox.
- `GET /api/sandboxes`: List all sandboxes.
- `DELETE /api/sandboxes/{name}`: Delete a specific sandbox.
- `GET /api/jobs`: List scheduled jobs.

---

## Testing with Postman

1. Use the `/auth/login` endpoint to authenticate and get an access token.
2. Add the access token to the `Authorization` header:
   ```
   Authorization: Bearer <access-token>
   ```
3. Test protected endpoints like `/api/test` or `/api/sandboxes`.

---

## Future Enhancements

- Add frontend integration using Next.js.
- Extend sandbox management capabilities.
- Implement advanced monitoring and alerting.

---

## License
This project is licensed under the MIT License.


