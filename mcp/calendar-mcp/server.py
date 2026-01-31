"""Google Calendar MCP Server for managing calendar events."""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from mcp.server import Server
from mcp.types import Tool, TextContent

# Google Calendar API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

app = Server("calendar-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
CREDENTIALS_PATH = os.getenv("CALENDAR_CREDENTIALS_PATH", "./credentials/client_secrets.json")
TOKEN_PATH = os.getenv("CALENDAR_TOKEN_PATH", "./credentials/calendar_token.json")
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Calendar service (initialized on first use)
_calendar_service = None


def get_calendar_service():
    """Get or create Google Calendar API service."""
    global _calendar_service

    if _calendar_service is not None:
        return _calendar_service

    if not CALENDAR_AVAILABLE:
        raise RuntimeError("Google Calendar API libraries not installed")

    creds = None
    token_path = Path(TOKEN_PATH)
    credentials_path = Path(CREDENTIALS_PATH)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Credentials not found: {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    _calendar_service = build('calendar', 'v3', credentials=creds)
    return _calendar_service


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "CalendarMCP",
        "event": action,
        **details
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []

    logs.append(entry)
    log_file.write_text(json.dumps(logs, indent=2))


def format_event(event: dict) -> str:
    """Format a calendar event for display."""
    start = event.get('start', {})
    end = event.get('end', {})

    start_time = start.get('dateTime', start.get('date', 'Unknown'))
    end_time = end.get('dateTime', end.get('date', 'Unknown'))

    summary = event.get('summary', 'No Title')
    location = event.get('location', '')
    description = event.get('description', '')
    attendees = event.get('attendees', [])

    result = f"- **{summary}**\n"
    result += f"  Start: {start_time}\n"
    result += f"  End: {end_time}\n"

    if location:
        result += f"  Location: {location}\n"
    if attendees:
        attendee_emails = [a.get('email', '') for a in attendees[:5]]
        result += f"  Attendees: {', '.join(attendee_emails)}\n"
    if description:
        result += f"  Notes: {description[:100]}...\n" if len(description) > 100 else f"  Notes: {description}\n"

    return result


async def _list_events(days: int = 7, max_results: int = 20) -> str:
    """List upcoming calendar events."""
    log_action("list_events_requested", {"days": days, "max_results": max_results})

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

        if not events:
            return f"No events found in the next {days} days."

        result = f"**Upcoming Events (next {days} days):**\n\n"
        for event in events:
            result += format_event(event) + "\n"

        log_action("list_events_success", {"event_count": len(events)})
        return result

    except Exception as e:
        log_action("list_events_failed", {"error": str(e)})
        return f"Failed to list events: {str(e)}"


async def _get_today_events() -> str:
    """Get today's calendar events."""
    log_action("get_today_events_requested", {})

    try:
        service = get_calendar_service()

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

        if not events:
            return "No events scheduled for today."

        result = f"**Today's Agenda ({now.strftime('%Y-%m-%d')}):**\n\n"
        for event in events:
            result += format_event(event) + "\n"

        log_action("get_today_events_success", {"event_count": len(events)})
        return result

    except Exception as e:
        log_action("get_today_events_failed", {"error": str(e)})
        return f"Failed to get today's events: {str(e)}"


async def _get_free_busy(days: int = 1) -> str:
    """Check free/busy status for the specified number of days."""
    log_action("get_free_busy_requested", {"days": days})

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

        if not busy_times:
            return f"You're free for the next {days} day(s)!"

        result = f"**Busy times (next {days} day(s)):**\n\n"
        for busy in busy_times:
            start = busy.get('start', 'Unknown')
            end = busy.get('end', 'Unknown')
            result += f"- {start} to {end}\n"

        log_action("get_free_busy_success", {"busy_count": len(busy_times)})
        return result

    except Exception as e:
        log_action("get_free_busy_failed", {"error": str(e)})
        return f"Failed to check free/busy: {str(e)}"


async def _create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: str = ""
) -> str:
    """Create a new calendar event."""
    log_action("create_event_requested", {
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create event:\nTitle: {summary}\nStart: {start_time}\nEnd: {end_time}\nLocation: {location}\nAttendees: {attendees}"

    try:
        service = get_calendar_service()

        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email.strip()} for email in attendees.split(',')]

        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()

        log_action("event_created", {
            "summary": summary,
            "event_id": created_event.get('id')
        })

        return f"Event created successfully!\nTitle: {summary}\nEvent ID: {created_event.get('id')}\nLink: {created_event.get('htmlLink')}"

    except Exception as e:
        log_action("create_event_failed", {"summary": summary, "error": str(e)})
        return f"Failed to create event: {str(e)}"


async def _update_event(
    event_id: str,
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = ""
) -> str:
    """Update an existing calendar event."""
    log_action("update_event_requested", {
        "event_id": event_id,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would update event {event_id}"

    try:
        service = get_calendar_service()

        # Get existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update fields if provided
        if summary:
            event['summary'] = summary
        if start_time:
            event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
        if end_time:
            event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
        if description:
            event['description'] = description
        if location:
            event['location'] = location

        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        log_action("event_updated", {"event_id": event_id})

        return f"Event updated successfully!\nEvent ID: {event_id}\nLink: {updated_event.get('htmlLink')}"

    except Exception as e:
        log_action("update_event_failed", {"event_id": event_id, "error": str(e)})
        return f"Failed to update event: {str(e)}"


async def _delete_event(event_id: str) -> str:
    """Delete a calendar event."""
    log_action("delete_event_requested", {
        "event_id": event_id,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would delete event {event_id}"

    try:
        service = get_calendar_service()

        service.events().delete(calendarId='primary', eventId=event_id).execute()

        log_action("event_deleted", {"event_id": event_id})

        return f"Event {event_id} deleted successfully."

    except Exception as e:
        log_action("delete_event_failed", {"event_id": event_id, "error": str(e)})
        return f"Failed to delete event: {str(e)}"


@app.list_tools()
async def handle_list_tools():
    """List available Calendar tools."""
    return [
        Tool(
            name="list_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to look ahead (default: 7)", "default": 7},
                    "max_results": {"type": "integer", "description": "Maximum number of events to return (default: 20)", "default": 20}
                },
                "required": []
            }
        ),
        Tool(
            name="get_today_events",
            description="Get today's calendar events (agenda view)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_free_busy",
            description="Check availability/free-busy status",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to check (default: 1)", "default": 1}
                },
                "required": []
            }
        ),
        Tool(
            name="create_event",
            description="Create a new calendar event (requires approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time in ISO format (e.g., 2026-02-01T10:00:00)"},
                    "end_time": {"type": "string", "description": "End time in ISO format (e.g., 2026-02-01T11:00:00)"},
                    "description": {"type": "string", "description": "Event description/notes", "default": ""},
                    "location": {"type": "string", "description": "Event location", "default": ""},
                    "attendees": {"type": "string", "description": "Comma-separated email addresses of attendees", "default": ""}
                },
                "required": ["summary", "start_time", "end_time"]
            }
        ),
        Tool(
            name="update_event",
            description="Update an existing calendar event (requires approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The event ID to update"},
                    "summary": {"type": "string", "description": "New event title", "default": ""},
                    "start_time": {"type": "string", "description": "New start time in ISO format", "default": ""},
                    "end_time": {"type": "string", "description": "New end time in ISO format", "default": ""},
                    "description": {"type": "string", "description": "New event description", "default": ""},
                    "location": {"type": "string", "description": "New event location", "default": ""}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="delete_event",
            description="Delete a calendar event (requires approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The event ID to delete"}
                },
                "required": ["event_id"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "list_events":
        result = await _list_events(
            days=arguments.get("days", 7),
            max_results=arguments.get("max_results", 20)
        )
    elif name == "get_today_events":
        result = await _get_today_events()
    elif name == "get_free_busy":
        result = await _get_free_busy(days=arguments.get("days", 1))
    elif name == "create_event":
        result = await _create_event(
            summary=arguments["summary"],
            start_time=arguments["start_time"],
            end_time=arguments["end_time"],
            description=arguments.get("description", ""),
            location=arguments.get("location", ""),
            attendees=arguments.get("attendees", "")
        )
    elif name == "update_event":
        result = await _update_event(
            event_id=arguments["event_id"],
            summary=arguments.get("summary", ""),
            start_time=arguments.get("start_time", ""),
            end_time=arguments.get("end_time", ""),
            description=arguments.get("description", ""),
            location=arguments.get("location", "")
        )
    elif name == "delete_event":
        result = await _delete_event(event_id=arguments["event_id"])
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
