# Approved Folder Processor - Setup Guide

## Overview

The `Approved/` folder watcher automatically processes files that have been approved for execution. This guide explains how it works and how to set up credentials.

## Architecture

```
Inbox/ → Needs_Action/ → Pending_Approval/ → Approved/ → (Processor) → Done/
                                                   ↑
                                            approved_watcher.py (every 5s)
```

## What Changed

### 1. Fixed Type Mismatch Bug
**File:** `backend/api/approvals.py`

The approval system now supports multiple action types:
- `social_post` - Social media posts
- `social` - Alternative social post type
- `whatsapp` - WhatsApp messages
- `email` - Email messages

### 2. Created Approved Folder Watcher
**File:** `watchers/approved_watcher.py`

A new watcher that:
- Monitors `Approved/` folder every 5 seconds
- Processes files using the Publisher service
- Moves completed files to `Done/`
- Logs all actions to `Logs/YYYY-MM-DD.json`

### 3. MCP Integration for Publishing
**File:** `backend/services/publisher.py`

Publisher now uses MCP tools instead of direct API calls:
- Facebook → `mcp__facebook__post_to_page`
- LinkedIn → `mcp__linkedin__create_post`
- Instagram → `mcp__instagram__post_image`
- Twitter → `mcp__twitter__create_tweet`
- WhatsApp → `mcp__whatsapp__send_message`
- Email → `mcp__gmail__send_email`

### 4. Credential Validation Endpoint
**File:** `backend/api/status.py`

New endpoint `GET /api/status/credentials` returns:
- Which platforms are configured
- Missing credentials/required files
- DRY_RUN mode status
- Count of files in Approved/ folder

## Configuration

### Step 1: Set DRY_RUN=false for Real Actions

Edit `.env` file:
```bash
DRY_RUN=false
```

When `DRY_RUN=true`:
- Actions are simulated
- Logs show `[DRY RUN]` prefix
- No actual posts/messages sent

### Step 2: Configure Platform Credentials

#### Facebook
```bash
FACEBOOK_PAGE_ACCESS_TOKEN=your_token_here
FACEBOOK_PAGE_ID=your_page_id_here
```

Get from: https://developers.facebook.com/tools/explorer/

#### LinkedIn
```bash
LINKEDIN_ACCESS_TOKEN=your_token_here
```

Get from: https://www.linkedin.com/developers/tools

#### Instagram
```bash
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id_here
```

Note: Instagram must be connected to a Facebook Page

#### Twitter/X
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

Get from: https://developer.twitter.com/en/portal/dashboard

#### WhatsApp
WhatsApp uses browser-based authentication:
1. Run WhatsApp MCP server: `python -m mcp.whatsapp_mcp`
2. Scan QR code on your phone
3. Session saved to `./credentials/whatsapp_session`

#### Gmail
Gmail uses OAuth token file:
1. Run Gmail MCP server: `python -m mcp.gmail_mcp`
2. Complete OAuth flow in browser
3. Token saved to `./credentials/gmail_token.json`

## Current State

You have **24 files** in the `Approved/` folder that are pending execution.

To check credential status:
```bash
curl http://localhost:8000/api/status/credentials
```

Or in the dashboard:
- Visit the Status page
- Look for "Credentials" section

## Testing

To test without actually posting:

1. Keep `DRY_RUN=true` in `.env`
2. Add a test file to `Approved/`
3. Watch logs in `Logs/YYYY-MM-DD.json`
4. Verify file moves to `Done/` with `[DRY RUN]` status

To enable real posting:
1. Set `DRY_RUN=false` in `.env`
2. Restart the backend
3. Files will be executed for real

## Monitoring

Check the status:
```bash
curl http://localhost:8000/api/status
```

Response includes:
```json
{
  "system": "running",
  "approved_count": 24,
  "pending_approvals": 0,
  "watchers": {
    "approved": "running",
    ...
  }
}
```

## Troubleshooting

### Files Not Being Processed

1. Check if approved watcher is running:
   ```bash
   curl http://localhost:8000/api/status | grep approved
   ```

2. Check logs for errors:
   ```bash
   cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
   ```

3. Verify DRY_RUN setting:
   ```bash
   grep DRY_RUN .env
   ```

### Credential Errors

Check which platforms are configured:
```bash
curl http://localhost:8000/api/status/credentials
```

Look for `"configured": false` entries.

### WhatsApp Profile Lock Error

If you see "Profile already in use" error:
1. Stop all WhatsApp browser sessions
2. Remove `./credentials/whatsapp_session/SingletonLock`
3. Restart the backend

## Manual Execution

To manually execute a specific approved file:
```bash
curl -X POST http://localhost:8000/api/approvals/publish/{filename}
```

To move a file to Done without executing:
```bash
curl -X POST http://localhost:8000/api/approvals/execute/{filename}
```
