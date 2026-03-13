# BugTracker+ (Jira-like Issue Tracking System)

BugTracker+ is a Jira-inspired cloud-native issue management platform built with FastAPI, React, MongoDB (CosmosDB compatible), Docker, GitHub Actions, and Azure-ready deployment workflows.

## Implemented Stack

- **Backend**: Python FastAPI + REST + JWT + RBAC
- **Frontend**: React.js + React Router + Axios + Tailwind CSS (Vite)
- **Database**: MongoDB / Azure Cosmos DB (Mongo API)
- **Testing**: PyTest + Selenium + Allure reports
- **DevOps**: Docker, docker-compose, GitHub Actions CI/CD, Azure deployment integration

## Jira-like Features Included

- Authentication: register/login/JWT
- Role permissions: `admin`, `project_manager`, `developer`, `tester`
- User profiles and role updates
- Projects and team membership management
- Issues with:
  - title, description, issue type (`bug`, `task`, `story`, `epic`)
  - status (`todo`, `in_progress`, `done`)
  - priority (`low`, `medium`, `high`, `critical`)
  - issue keys (`AUTH-1`, `AUTH-2`, ...)
  - reporter, assignee, labels
  - attachments
  - timestamps and history tracking
- Kanban board with dnd-kit drag/drop status updates
- Sprint management (create/start/close)
- Backlog prioritization with drag reorder + drag to sprint targets
- Threaded comments with edit/delete
- Issue activity timeline (`issue_activity`) + audit timeline
- Search and filters (status/priority/project/assignee/labels/text)
- Issue linking (`blocks`, `blocked_by`, `relates_to`, `duplicates`)
- Notifications for assignment/comments/status changes
- Project workspace routes (`/project/:key`) with tabs:
  - Issues, Board, Backlog, Reports, Members, Settings
- Reports & charts (status, priority, burndown, velocity)
- Dashboard statistics + recent activity + assigned-to-me
- Optional demo seed script with 50 AUTH issues (including Epic/Story)

## Repository Structure

```text
bugtracker-plus/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── models/
│   │   ├── services/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── db/
│   │   └── database.py
│   ├── tests/
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── context/
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## Run Locally

### Option A: Docker Compose (recommended)

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- MongoDB: `mongodb://localhost:27017`

`docker-compose.yml` enables demo seed data by default (`BUGTRACKER_ENABLE_DEMO_SEED=true`).
Backend defaults to MongoDB storage (`BUGTRACKER_STORE_BACKEND=mongodb`) to persist issue updates/comments/status changes.

### Option B: Run services separately

Backend:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python3 -m uvicorn app.main:app --reload --app-dir backend --host 0.0.0.0 --port 8000
```

Frontend:
```bash
npm --prefix frontend install
cp frontend/.env.example frontend/.env
npm --prefix frontend run dev
```

### Seed demo data manually

```bash
npm run seed:demo
```

Default seeded users:
- `admin@jira.com` / `Password123!`
- `pm@jira.com` / `Password123!`
- `dev@jira.com` / `Password123!`
- `qa@jira.com` / `Password123!`

## API Summary

- **Auth**
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- **Users**
  - `GET /users`
  - `GET /users/{id}`
  - `PUT /users/me/profile`
  - `PUT /users/{id}/role`
- **Projects**
  - `POST /projects`
  - `GET /projects`
  - `GET /projects/key/{key}`
  - `GET /projects/{id}`
  - `PUT /projects/{id}`
  - `POST /projects/{id}/members`
  - `GET /projects/{id}/dashboard`
  - `GET /projects/{id}/reports`
  - `GET /projects/{id}/backlog`
  - `PUT /projects/{id}/backlog/reorder`
  - `GET /projects/{id}/board`
- **Issues**
  - `POST /issues`
  - `GET /issues`
  - `GET /issues/key/{issueKey}`
  - `GET /issues/{id}`
  - `PUT /issues/{id}`
  - `DELETE /issues/{id}`
  - `PUT /issues/{id}/sprint`
  - `POST /issues/{id}/attachments`
  - `GET /issues/{id}/activity`
  - `GET /issues/{id}/links`
  - `POST /issues/{id}/links`
  - `DELETE /issues/{id}/links/{linkId}`
- **Comments**
  - `POST /comments`
  - `GET /comments/{issueId}`
  - `PUT /comments/{commentId}`
  - `DELETE /comments/{commentId}`
- **Sprints**
  - `POST /sprints`
  - `GET /sprints`
  - `PUT /sprints/{id}`
  - `POST /sprints/{id}/start`
  - `POST /sprints/{id}/close`
- **System**
  - `GET /dashboard`
  - `GET /audit`
  - `GET /notifications`
  - `PUT /notifications/{id}/read`
  - `GET /health`

## Testing

Backend:
```bash
PYTHONPATH=backend python3 -m pytest backend/tests -q
```

Allure report artifacts:
```bash
PYTHONPATH=backend python3 -m pytest backend/tests --alluredir=backend/allure-results
```

Selenium E2E:
```bash
E2E_FRONTEND_URL=http://localhost:5173 PYTHONPATH=backend python3 -m pytest backend/tests -m e2e -q
```

## CI/CD and Azure

GitHub Actions (`.github/workflows/ci.yml`) performs:
- frontend install/lint/build
- backend test execution
- Allure artifacts upload
- docker image build validation
- optional Azure deployment on `main` using:
  - `AZURE_CREDENTIALS`
  - `AZURE_WEBAPP_NAME`
  - `AZURE_WEBAPP_IMAGE`

### Azure service mapping
- **Azure App Service**: host backend container
- **Azure Cosmos DB (Mongo API)**: primary database
- **Azure Blob Storage**: issue attachment storage (optional env-enabled)
- **Azure Monitor**: application and platform monitoring
