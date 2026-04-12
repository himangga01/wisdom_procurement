from fastapi import APIRouter

from app.api.routes import analyses, corporations, dashboard, documents, projects

api_router = APIRouter()
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(corporations.router, prefix="/corporations", tags=["corporations"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
