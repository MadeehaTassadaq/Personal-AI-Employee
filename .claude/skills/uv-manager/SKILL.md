# UV Package Manager Skill

This skill manages the Python project using the `uv` package manager for fast dependency resolution and installation.

## Capabilities

- Install project dependencies using `uv`
- Run the backend server using `uv`
- Run tests using `uv`
- Manage virtual environments using `uv`

## Commands

### Install Dependencies
```bash
uv sync
```

### Run Backend Server
```bash
uv run python -m backend.main
```

### Run Tests
```bash
uv run pytest
```

### Run File Watcher
```bash
uv run python -m watchers.file_watcher ./AI_Employee_Vault
```

### Run All Watchers
```bash
uv run python -m backend.main & uv run python -m watchers.file_watcher ./AI_Employee_Vault
```

## Requirements

- `uv` package manager installed on the system

## Usage Examples

- "Install dependencies with uv"
- "Run the backend server using uv"
- "Run tests with uv"
- "Start the file watcher using uv"