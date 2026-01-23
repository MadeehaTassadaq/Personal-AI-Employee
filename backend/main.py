"""FastAPI backend for Digital FTE orchestration."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables BEFORE importing modules that use them
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import status, watchers, vault, approvals

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"[BACKEND] Starting Digital FTE API")
    print(f"[BACKEND] Vault path: {VAULT_PATH}")

    # Ensure vault directories exist
    for folder in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs", "Plans"]:
        (VAULT_PATH / folder).mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("[BACKEND] Shutting down...")


app = FastAPI(
    title="Digital FTE API",
    description="Personal AI Employee orchestration API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(watchers.router, prefix="/api/watchers", tags=["Watchers"])
app.include_router(vault.router, prefix="/api/vault", tags=["Vault"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Digital FTE API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
