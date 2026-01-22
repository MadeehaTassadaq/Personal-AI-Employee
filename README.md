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
| Read vault files   | ✅           |                   |
| Move files         | ✅           |                   |
| Update Dashboard   | ✅           |                   |
| Create drafts      | ✅           |                   |
| Send email         |              | ✅                |
| Send WhatsApp msg  |              | ✅                |
| Post on LinkedIn   |              | ✅                |

## Agent Skills

Available skills in `.claude/skills/`:
- `read_vault.md` - Read vault files
- `write_task.md` - Create task files
- `move_task.md` - Move files between folders
- `weekly_briefing.md` - Generate executive summaries
- `send_email.md` - Send emails via Gmail
- `send_whatsapp.md` - Send WhatsApp messages
- `post_linkedin.md` - Post on LinkedIn

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

## License

MIT