from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.store import InMemoryStore, MongoStore
from app.routes import audit, auth, comments, dashboard, health, issues, projects, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.mongodb_uri:
        app.state.store = MongoStore(settings.mongodb_uri, settings.mongodb_db_name)
    else:
        app.state.store = InMemoryStore()
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

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
