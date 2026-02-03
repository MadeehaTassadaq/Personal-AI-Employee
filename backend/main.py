"""FastAPI backend for Digital FTE orchestration."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Set
 

from dotenv import load_dotenv

# Load environment variables BEFORE importing modules that use them
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api import status, watchers, vault, approvals, audit, ralph, ceo_briefing, odoo, social, calendar, trigger, compose, business_audit
from backend.services.audit_logger import get_audit_logger, AuditAction
from backend.services.ralph_wiggum import get_ralph
from backend.services.scheduler import init_scheduler, shutdown_scheduler

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        message_text = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"[BACKEND] Starting Digital FTE API (Gold Tier)")
    print(f"[BACKEND] Vault path: {VAULT_PATH}")

    # Ensure vault directories exist
    for folder in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs", "Plans", "Reports", "Audit"]:
        (VAULT_PATH / folder).mkdir(parents=True, exist_ok=True)

    # Initialize state.json if it doesn't exist
    state_file = Path(__file__).parent / "state.json"
    if not state_file.exists():
        default_state = {
            "system": "stopped",
            "watchers": {
                "file": "stopped",
                "gmail": "stopped",
                "whatsapp": "stopped",
                "linkedin": "stopped",
                "facebook": "stopped",
                "instagram": "stopped",
                "twitter": "stopped"
            },
            "last_updated": datetime.now().isoformat()
        }
        state_file.write_text(json.dumps(default_state, indent=2))
        print("[BACKEND] Initialized state.json with default values")

    # Initialize scheduler for periodic tasks
    init_scheduler()
    print("[BACKEND] Scheduler initialized")

    # Initialize audit logger
    audit_logger = get_audit_logger()
    audit_logger.log(
        AuditAction.SYSTEM_START,
        platform="system",
        actor="system",
        details={"vault_path": str(VAULT_PATH)}
    )

    # Set up Ralph Wiggum event handler
    ralph = get_ralph()
    ralph.on_event(lambda event, data: asyncio.create_task(
        manager.broadcast({"type": f"ralph_{event}", "data": data})
    ))

    yield

    # Shutdown
    print("[BACKEND] Shutting down...")
    shutdown_scheduler()
    print("[BACKEND] Scheduler stopped")
    audit_logger.log(
        AuditAction.SYSTEM_STOP,
        platform="system",
        actor="system"
    )


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
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(ralph.router, prefix="/api/ralph", tags=["Ralph Wiggum"])
app.include_router(ceo_briefing.router, prefix="/api/ceo-briefing", tags=["CEO Briefing"])
app.include_router(odoo.router, prefix="/api/odoo", tags=["Odoo Accounting"])
app.include_router(social.router, prefix="/api/social", tags=["Social Media"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(trigger.router, prefix="/api/trigger", tags=["Trigger"])
app.include_router(compose.router, prefix="/api/compose", tags=["Compose"])
app.include_router(business_audit.router, prefix="/api/business-audit", tags=["Business Audit"])


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


# WebSocket endpoint for real-time activity updates
@app.websocket("/ws/activity")
async def websocket_activity(websocket: WebSocket):
    """WebSocket endpoint for real-time activity updates.

    Clients receive:
    - watcher_event: Events from file/gmail/whatsapp/linkedin watchers
    - ralph_*: Events from Ralph Wiggum loop
    - system_*: System events
    """
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await manager.send_personal(websocket, {
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Digital FTE activity stream"
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (ping/pong, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping
                if data == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal(websocket, {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Function to broadcast events (called by watchers/services)
async def broadcast_activity(event_type: str, data: dict):
    """Broadcast an activity event to all connected WebSocket clients."""
    await manager.broadcast({
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    })


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
