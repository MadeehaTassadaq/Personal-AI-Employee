#!/usr/bin/env python3
"""
Google Calendar OAuth Setup Script
Run this to generate calendar_token.json for the Calendar MCP server.

Prerequisites:
1. Enable Google Calendar API in Google Cloud Console
2. Have client_secrets.json in the credentials folder
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
]

def main():
    project_root = Path(__file__).parent.parent
    credentials_path = project_root / 'credentials' / 'client_secrets.json'
    token_path = project_root / 'credentials' / 'calendar_token.json'

    print("=" * 50)
    print("Google Calendar OAuth Setup")
    print("=" * 50)
    print(f"\nUsing credentials: {credentials_path}")
    print(f"Token will be saved to: {token_path}")

    if not credentials_path.exists():
        print(f"\nERROR: {credentials_path} not found!")
        print("\nTo fix this:")
        print("1. Go to Google Cloud Console (console.cloud.google.com)")
        print("2. Select your project (same one used for Gmail)")
        print("3. Enable the Google Calendar API")
        print("4. Create OAuth 2.0 credentials (or use existing client_secrets.json)")
        return

    print("\nStarting OAuth flow...")
    print("A browser window will open for authentication.\n")

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=8081)

    # Save the token
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as f:
        f.write(creds.to_json())

    print(f"\nSuccess! Token saved to {token_path}")
    print("\nCalendar MCP server is now ready to use.")
    print("\nNext steps:")
    print("1. Restart Claude Code to load the new MCP server")
    print("2. Test with: list_events or get_today_events")

if __name__ == '__main__':
    main()
