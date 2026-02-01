"""Google Calendar API endpoints for the dashboard."""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# Resolve project root (go up from backend/api/ to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class CalendarEvent(BaseModel):
    """Calendar event model."""
    id: str
    summary: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None
    html_link: Optional[str] = None
    all_day: bool = False


class FreeBusySlot(BaseModel):
    """Free/busy time slot."""
    start: str
    end: str


# Check if Calendar API is available
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False


# Resolve credential paths relative to project root
_default_creds_path = str(PROJECT_ROOT / "credentials" / "client_secrets.json")
_default_token_path = str(PROJECT_ROOT / "credentials" / "calendar_token.json")
CREDENTIALS_PATH = os.getenv("CALENDAR_CREDENTIALS_PATH", _default_creds_path)
TOKEN_PATH = os.getenv("CALENDAR_TOKEN_PATH", _default_token_path)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

_calendar_service = None


def get_calendar_service():
    """Get or create Google Calendar API service (read-only)."""
    global _calendar_service

    if _calendar_service is not None:
        return _calendar_service

    if not CALENDAR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Calendar API libraries not installed")

    token_path = Path(TOKEN_PATH)

    if not token_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Calendar not configured. Run scripts/calendar_oauth.py first."
        )

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())

        _calendar_service = build('calendar', 'v3', credentials=creds)
        return _calendar_service

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Calendar auth error: {str(e)}")


def parse_event(event: dict) -> CalendarEvent:
    """Parse a Google Calendar event into our model."""
    start = event.get('start', {})
    end = event.get('end', {})

    # Check if all-day event
    all_day = 'date' in start

    start_time = start.get('dateTime', start.get('date', ''))
    end_time = end.get('dateTime', end.get('date', ''))

    attendees = []
    if 'attendees' in event:
        attendees = [a.get('email', '') for a in event['attendees']]

    return CalendarEvent(
        id=event.get('id', ''),
        summary=event.get('summary', 'No Title'),
        start=start_time,
        end=end_time,
        location=event.get('location'),
        description=event.get('description'),
        attendees=attendees if attendees else None,
        html_link=event.get('htmlLink'),
        all_day=all_day
    )


@router.get("/status")
async def calendar_status():
    """Check if calendar is configured and accessible."""
    token_path = Path(TOKEN_PATH)

    if not CALENDAR_AVAILABLE:
        return {
            "status": "unavailable",
            "error": "Google Calendar API libraries not installed",
            "configured": False
        }

    if not token_path.exists():
        return {
            "status": "not_configured",
            "error": "Run scripts/calendar_oauth.py to configure",
            "configured": False
        }

    try:
        service = get_calendar_service()
        # Quick API test
        service.calendarList().list(maxResults=1).execute()
        return {
            "status": "connected",
            "configured": True,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "configured": True
        }


@router.get("/today")
async def get_today_events():
    """Get today's calendar events for the dashboard."""
    try:
        service = get_calendar_service()

        # Get today's boundaries in UTC
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        return {
            "date": now.strftime('%Y-%m-%d'),
            "events": [parse_event(e).model_dump() for e in events],
            "count": len(events),
            "fetched_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get("/events")
async def list_events(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to look ahead"),
    max_results: int = Query(default=20, ge=1, le=100, description="Maximum events to return")
):
    """List upcoming calendar events."""
    try:
        service = get_calendar_service()

        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        return {
            "days": days,
            "events": [parse_event(e).model_dump() for e in events],
            "count": len(events),
            "time_range": {
                "start": time_min,
                "end": time_max
            },
            "fetched_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get("/free-busy")
async def get_free_busy(
    days: int = Query(default=1, ge=1, le=7, description="Number of days to check")
):
    """Check free/busy status."""
    try:
        service = get_calendar_service()

        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": "primary"}]
        }

        freebusy_result = service.freebusy().query(body=body).execute()

        busy_times = freebusy_result.get('calendars', {}).get('primary', {}).get('busy', [])

        return {
            "days": days,
            "busy_slots": [
                FreeBusySlot(start=b['start'], end=b['end']).model_dump()
                for b in busy_times
            ],
            "busy_count": len(busy_times),
            "time_range": {
                "start": time_min,
                "end": time_max
            },
            "fetched_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check free/busy: {str(e)}")


@router.get("/event/{event_id}")
async def get_event(event_id: str):
    """Get a specific calendar event by ID."""
    try:
        service = get_calendar_service()

        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()

        return {
            "event": parse_event(event).model_dump(),
            "fetched_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch event: {str(e)}")
