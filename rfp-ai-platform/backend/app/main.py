import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routers import auth, documents, retrieval, rfp, generation, export, projects, workflow, assistant

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS for local development with React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(retrieval.router, prefix=settings.API_V1_STR)
app.include_router(rfp.router, prefix=settings.API_V1_STR)
app.include_router(generation.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(workflow.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
def root():
    return {"message": "Welcome to the AI-Powered RFP Intelligence API"}
