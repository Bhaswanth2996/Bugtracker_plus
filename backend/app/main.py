from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db.store import InMemoryStore, MongoStore
from app.routes import ai_platform, audit, auth, comments, dashboard, health, issues, notifications, projects, sprints, users
from app.services.seeder import seed_demo_data

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.local_upload_dir).mkdir(parents=True, exist_ok=True)
    if settings.store_backend == "memory":
        app.state.store = InMemoryStore()
    elif settings.store_backend == "mongodb":
        app.state.store = MongoStore(settings.mongodb_uri, settings.mongodb_db_name)
    else:
        raise RuntimeError(
            "Invalid BUGTRACKER_STORE_BACKEND. Supported values: mongodb, memory"
        )
    if settings.enable_demo_seed:
        seed_demo_data(app.state.store)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.local_upload_dir), name="uploads")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(issues.project_router)
app.include_router(comments.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(dashboard.project_router)
app.include_router(sprints.router)
app.include_router(sprints.project_router)
app.include_router(notifications.router)
app.include_router(ai_platform.router)
