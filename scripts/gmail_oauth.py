#!/usr/bin/env python3
"""
Gmail OAuth Setup Script
Run this to generate gmail_token.json for the Gmail MCP server.
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
]

def main():
    project_root = Path(__file__).parent.parent
    credentials_path = project_root / 'credentials' / 'client_secrets.json'
    token_path = project_root / 'credentials' / 'gmail_token.json'

    print(f"Using credentials: {credentials_path}")
    print(f"Token will be saved to: {token_path}")

    if not credentials_path.exists():
        print(f"ERROR: {credentials_path} not found!")
        print("Create it with your Google OAuth client ID and secret.")
        return

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=8080)

    # Save the token
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as f:
        f.write(creds.to_json())

    print(f"\nSuccess! Token saved to {token_path}")
    print("Gmail MCP server is now ready to use.")

if __name__ == '__main__':
    main()
