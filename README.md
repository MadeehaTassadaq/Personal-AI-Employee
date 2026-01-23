# Digital FTE - Personal AI Employee (Silver Tier)

A comprehensive AI employee system that operates through an Obsidian vault, with web dashboard and MCP server integrations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOU (CEO)                                  │
│                    Views Web Dashboard                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                    WEB DASHBOARD (React)                           │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐       │
│   │ Status   │ │ Watchers │ │ Approvals│ │ Activity Feed │       │
│   └──────────┘ └──────────┘ └──────────┘ └───────────────┘       │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────────────┐
│                    FASTAPI BACKEND (Orchestrator)                    │
│         Manages watchers, state, triggers Claude                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────────────────┐
│   WATCHERS    │  │ OBSIDIAN VAULT│  │        MCP SERVERS            │
│ ┌───────────┐ │  │ (Memory)      │  │ ┌─────────┐ ┌─────────────┐  │
│ │ Filesystem│ │  │               │  │ │ Gmail   │ │ WhatsApp    │  │
│ │ Gmail     │ │  │ Inbox/        │  │ │ MCP     │ │ MCP         │  │
│ │ WhatsApp  │ │  │ Needs_Action/ │  │ └─────────┘ └─────────────┘  │
│ │ LinkedIn  │ │  │ Pending_      │  │ ┌─────────┐ ┌─────────────┐  │
│ └───────────┘ │  │   Approval/   │  │ │LinkedIn │ │ Browser     │  │
│               │  │ Done/         │  │ │ MCP     │ │ MCP         │  │
└───────────────┘  └───────────────┘  │ └─────────┘ └─────────────┘  │
        │                   │          └───────────────────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                    CLAUDE CODE (Brain)                              │
│         Uses Agent Skills + MCP tools to process & act               │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Web Dashboard**: React-based UI for monitoring and control
- **Task Lifecycle**: Inbox → Needs Action → Pending Approval → Done
- **Multiple Watchers**: File system, Gmail, WhatsApp, LinkedIn
- **Human-in-the-Loop**: Approval workflow for sensitive actions
- **MCP Integration**: Secure external service actions via MCP protocol
- **Audit Trail**: Complete logging of all actions

## Setup

### Prerequisites
- Python 3.13
- Node.js 18+
- uv package manager
- Claude Code CLI

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd personal-ai-employee
```

2. Install Python dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

3. Install Playwright for WhatsApp:
```bash
playwright install chromium
```

4. Install Node.js dependencies:
```bash
cd dashboard
npm install
```

5. Copy and configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### MCP Server Configuration

Copy the MCP config:
```bash
cp mcp-config.json .mcp-config.json
```

## Connecting to Your Obsidian Vault

By default, the system uses a local `./vault` folder. To connect to your existing Obsidian vault:

### Option 1: Update VAULT_PATH (Recommended)

Edit your `.env` file to point to your Obsidian vault:

```bash
# Change from:
VAULT_PATH=./vault

# To your Obsidian vault path:
VAULT_PATH=/home/username/Documents/MyObsidianVault
```

Then create the required folder structure inside your Obsidian vault:

```bash
# Navigate to your Obsidian vault
cd /path/to/your/obsidian/vault

# Create required folders
mkdir -p Inbox Needs_Action Pending_Approval Approved Done Logs Plans

# Create required files (if they don't exist)
touch Dashboard.md Company_Handbook.md
```

Your vault should have this structure:
```
your-obsidian-vault/
├── Inbox/              # New incoming tasks
├── Needs_Action/       # Tasks being processed
├── Pending_Approval/   # Actions awaiting approval
├── Approved/           # Approved actions ready to execute
├── Done/               # Completed tasks
├── Logs/               # Activity logs
├── Plans/              # Generated briefings
├── Dashboard.md        # Status overview
└── Company_Handbook.md # Rules and guidelines
```

### Option 2: Symlink Approach

Create a symbolic link from the project's vault folder to your Obsidian vault:

```bash
# Remove the default vault folder
rm -rf vault

# Create symlink to your Obsidian vault
ln -s /path/to/your/obsidian/vault ./vault
```

### Option 3: Use Obsidian Vault Subfolder

If you don't want to modify your entire Obsidian vault, create a dedicated subfolder:

```bash
# In your Obsidian vault, create a Digital-FTE folder
mkdir -p /path/to/obsidian/vault/Digital-FTE

# Set VAULT_PATH to this subfolder
VAULT_PATH=/path/to/obsidian/vault/Digital-FTE
```

## Google Cloud Console Setup (Gmail API)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: "Desktop App" (recommended) or "Web application"
5. Configure redirect URIs:
   - For Desktop App: `http://localhost:8080`
   - For Web App: `http://localhost:8000/oauth/callback`
6. Download the credentials JSON
7. Copy Client ID and Client Secret to your `.env` file

## Usage

### Quick Start
```bash
# Start all services
./scripts/run_all.sh
```

### Individual Services

Start backend only:
```bash
./scripts/run_backend.sh
```

Start watchers only:
```bash
./scripts/run_watchers.sh
```

Start dashboard only:
```bash
./scripts/run_dashboard.sh
```

## Configuration

### Environment Variables

- `VAULT_PATH`: Path to Obsidian vault (default: `./vault`)
- `API_PORT`: Backend API port (default: 8000)
- `DRY_RUN`: Set to `false` to enable real actions (default: `true`)
- `GMAIL_REDIRECT_URI`: OAuth redirect URI (default: `http://localhost:8080`)
- Service-specific credentials (see `.env.example`)

### MCP Services

The system uses MCP (Model Context Protocol) servers for external actions:

- **Gmail MCP**: Send emails via Gmail API
- **WhatsApp MCP**: Send messages via WhatsApp Web
- **LinkedIn MCP**: Post content to LinkedIn
- **Browser MCP**: General browser automation

## Task Lifecycle

1. **Inbox/** - New tasks arrive here
2. **Needs_Action/** - Tasks being processed
3. **Pending_Approval/** - Actions awaiting human approval
4. **Approved/** - Approved actions ready to execute
5. **Done/** - Completed tasks with completion notes

## Approval Matrix

| Action Type        | Auto-Approve | Requires Approval |
|--------------------|--------------|-------------------|
| Read vault files   | Yes          |                   |
| Move files         | Yes          |                   |
| Update Dashboard   | Yes          |                   |
| Create drafts      | Yes          |                   |
| Send email         |              | Yes               |
| Send WhatsApp msg  |              | Yes               |
| Post on LinkedIn   |              | Yes               |

## Agent Skills

Available skills in `.claude/skills/` (Anthropic format):

| Skill | Description |
|-------|-------------|
| `vault-reader/` | Read and summarize vault files |
| `task-writer/` | Create new task files |
| `task-mover/` | Move tasks between lifecycle folders |
| `weekly-briefing/` | Generate executive CEO briefings |
| `email-sender/` | Send emails via Gmail MCP |
| `whatsapp-sender/` | Send WhatsApp messages via MCP |
| `linkedin-poster/` | Post to LinkedIn via MCP |
| `skill-creator/` | Create new skills (meta-skill) |

## Security

- All external actions go through MCP servers
- Dry-run mode enabled by default
- Approval workflow for sensitive actions
- Complete audit logging
- Credential isolation

## Development

### Adding New MCP Services

1. Create new MCP server in `mcp/service-name-mcp/`
2. Add to `mcp-config.json`
3. Create corresponding skill in `.claude/skills/`

### Customizing Watchers

1. Extend from `watchers/base_watcher.py`
2. Implement `check_for_updates()` and `on_new_item()`
3. Add to startup script

## Troubleshooting

- Check logs in `vault/Logs/`
- Verify MCP server connections
- Ensure all environment variables are set
- Confirm Claude Code is accessible
- For OAuth issues, verify redirect URIs match in `.env` and Google Cloud Console

## License

MIT
