from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import complaints, capa, copilot

# Creates tables if they don't exist. For anything beyond local dev,
# switch to Alembic migrations (alembic/ folder can be added with
# `alembic init alembic`).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIVOA Complaint Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(capa.router)
app.include_router(copilot.router)


@app.get("/health")
def health():
    return {"status": "ok"}
