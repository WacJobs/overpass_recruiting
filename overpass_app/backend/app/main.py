from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.companies import router as companies_router
from app.api.routes.health import router as health_router
from app.api.routes.matches import router as matches_router
from app.core.config import get_settings
from app.db.database import Base, engine
import app.models  # noqa: F401

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(health_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(matches_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs"}
