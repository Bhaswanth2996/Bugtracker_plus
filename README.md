# Bug Tracker+

Bug Tracker+ is a full-stack, cloud-ready issue management platform built for Agile and DevOps workflows.

## Tech Stack

- **Frontend**: Next.js (React + TypeScript + Tailwind CSS)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (with in-memory fallback for local dev/testing)
- **Auth**: JWT-based authentication with role-based access control (RBAC)
- **DevOps**: Docker Compose + GitHub Actions CI

## Features Implemented

- User registration/login and JWT auth
- Bootstrap admin creation (first registered account becomes admin)
- Role-aware access: `admin`, `manager`, `developer`, `tester`
- Project management (create/list/update)
- Issue management:
  - create/list/filter/get/update
  - status transitions (`open`, `in_progress`, `resolved`, `closed`)
  - priorities (`low`, `medium`, `high`, `critical`)
  - assignment and tags
  - change history tracking
- Commenting on issues
- Audit logging for key actions
- Dashboard stats for issue metrics
- Cloud-ready and local Docker setup

## Repository Layout

```text
.
├── app/                      # Next.js frontend
├── backend/
│   ├── app/
│   │   ├── core/             # config, auth, dependencies
│   │   ├── db/               # Mongo/in-memory store implementations
│   │   ├── models/           # Pydantic schemas
│   │   ├── routes/           # API routers
│   │   └── services/         # supporting services (audit)
│   ├── tests/                # backend pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── Dockerfile.frontend
└── .github/workflows/ci.yml
```

## Local Development

### 1) Frontend setup

```bash
npm ci
cp .env.example .env.local
npm run dev:frontend
```

Frontend runs on `http://localhost:3000`.

### 2) Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
npm run dev:backend
```

Backend runs on `http://localhost:8000`.

### 3) Docker full-stack setup

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- MongoDB: `mongodb://localhost:27017`

## API Overview

- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/users`
- `PATCH /api/users/{user_id}/role`
- `POST /api/projects`
- `GET /api/projects`
- `PATCH /api/projects/{project_id}`
- `POST /api/issues`
- `GET /api/issues`
- `GET /api/issues/{issue_id}`
- `PATCH /api/issues/{issue_id}`
- `POST /api/comments`
- `GET /api/comments/issue/{issue_id}`
- `GET /api/audit`
- `GET /api/dashboard/stats`

## Testing and Validation

### Backend tests

```bash
npm run test:backend
```

### Frontend lint/build

```bash
npm run lint
npm run build
```

## CI

GitHub Actions pipeline (`.github/workflows/ci.yml`) runs:
- frontend lint + build
- backend pytest tests

## Azure Deployment Notes

For your final project target:
- Deploy backend container to Azure App Service
- Use Azure Cosmos DB for MongoDB API
- Deploy frontend (Next.js) to Azure Static Web Apps or App Service
- Store secrets in Azure Key Vault/App Service settings
- Keep CI/CD in GitHub Actions or Azure DevOps pipelines
