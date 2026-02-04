# CLI Design Best Practices

## Command Naming Conventions

### Use Natural Language Verbs
**Good:**
- `add task "Buy milk"`
- `list tasks`
- `delete task 1`
- `show task 1`
- `update task 1 --title "Buy eggs"`

**Bad:**
- `create-entry --type=task --content="Buy milk"`
- `query --entity=task`
- `remove --id=1`
- `fetch --resource=task --id=1`

### Consistent Structure Patterns

**Pattern 1: Verb-Noun**
```
app add task
app list tasks
app delete task
app show project
```

**Pattern 2: Noun-Verb (Resource-Action)**
```
app task add
app task list
app task delete
app project show
```

**Choose one pattern and stick to it consistently.**

### Abbreviations and Aliases

**Guideline:** Provide both full and abbreviated forms

**Good:**
```
app list       (or app ls)
app add        (or app a)
app delete     (or app rm)
```

**Bad:**
```
app lst        (only abbreviated form)
app rmv        (non-standard abbreviation)
```

---

## Argument Design

### Favor Positional Arguments for Required Inputs

**Good:**
```
app add task "Buy milk"
app delete task 1
```

**Bad:**
```
app add --type=task --content="Buy milk"
app delete --entity=task --id=1
```

### Use Flags for Optional Inputs

**Good:**
```
app add task "Buy milk" --due tomorrow --priority high
app list tasks --status incomplete
```

**Bad:**
```
app add "Buy milk" --task --due tomorrow --priority high
```

### Boolean Flags Should Not Require Values

**Good:**
```
app list --completed
app build --watch
app deploy --dry-run
```

**Bad:**
```
app list --completed=true
app build --watch=yes
app deploy --dry-run=true
```

---

## Help and Documentation

### Provide Multi-Level Help

**Global Help:**
```
$ app --help
Todo App - Manage your tasks efficiently

USAGE:
  app <command> [options]

COMMANDS:
  add        Add a new task
  list       List all tasks
  delete     Delete a task
  complete   Mark a task as complete

Run 'app <command> --help' for command-specific help.
```

**Command-Specific Help:**
```
$ app add --help
Add a new task

USAGE:
  app add <title> [options]

ARGUMENTS:
  <title>    Task title (required)

OPTIONS:
  --due <date>       Due date (e.g., tomorrow, 2024-01-15)
  --priority <level> Priority: low, medium, high (default: medium)
  --tags <tags>      Comma-separated tags

EXAMPLES:
  app add "Buy milk"
  app add "Finish report" --due tomorrow --priority high
  app add "Review PR" --tags work,urgent
```

### Include Examples in Help Text

Every command help should include:
1. Basic usage example
2. Common option combinations
3. Edge case examples (if relevant)

---

## Defaults and Configuration

### Zero-Config First Run

**Good:**
```
$ app
Welcome to Todo App! (No config file found, using defaults)

You have 0 tasks.

Try: app add "My first task"
```

**Bad:**
```
$ app
Error: Configuration file 'config.json' not found.
Run 'app init' to create configuration.
```

### Sensible Defaults Checklist

- [ ] App works without config file
- [ ] Common use case works with minimal input
- [ ] Default output format is human-readable
- [ ] Interactive mode asks for required values
- [ ] Can defer advanced configuration

### Progressive Configuration

**Level 0: Zero Config**
```
app add "Buy milk"
# Works immediately with defaults
```

**Level 1: Simple Config**
```
app config set default-priority high
# Single setting for frequent customization
```

**Level 2: Advanced Config**
```
app config edit
# Opens full config file for power users
```

---

## Error Messages

### Good Error Messages Have Three Parts

1. **What went wrong**
2. **Why it went wrong**
3. **How to fix it**

**Good:**
```
Error: Command 'lst' not found.

Did you mean 'list'?

Run 'app --help' to see all commands.
```

**Bad:**
```
Error: Invalid command
```

### Typo Suggestions

**Implement fuzzy matching for command names:**

```python
def suggest_command(input_cmd, valid_commands):
    from difflib import get_close_matches
    matches = get_close_matches(input_cmd, valid_commands, n=1, cutoff=0.6)
    return matches[0] if matches else None
```

**Output:**
```
Error: Command 'dlete' not found. Did you mean 'delete'?
```

### Actionable Error Messages

**Good:**
```
Error: Task #5 does not exist.

You have 3 tasks (IDs: 1, 2, 3).
Run 'app list' to see all tasks.
```

**Bad:**
```
Error: Invalid task ID
```

---

## Interactive vs Non-Interactive Modes

### Non-Interactive (Default)

**For automation and scripting:**
```
app add "Task title" --due tomorrow --priority high
# Returns immediately, prints confirmation
```

### Interactive (Opt-In)

**For guided workflows:**
```
$ app add --interactive
Task title: Buy milk
Due date (optional): tomorrow
Priority [low/medium/high]: medium
Tags (optional):

✓ Task added: Buy milk (due tomorrow)
```

### Detection

```python
import sys

def is_interactive():
    return sys.stdin.isatty() and sys.stdout.isatty()

# Use interactive prompts only when appropriate
if is_interactive() and missing_required_input:
    value = input("Task title: ")
else:
    print("Error: Task title required")
    sys.exit(1)
```

---

## Feedback and Progress

### Immediate Feedback

**Every action should provide clear feedback:**

**Good:**
```
$ app add "Buy milk"
✓ Task added: Buy milk (ID: 4)

$ app delete 4
✓ Task #4 deleted: Buy milk
```

**Bad:**
```
$ app add "Buy milk"
(no output)

$ app delete 4
(no output)
```

### Progress Indicators

**For long-running operations:**

**Good:**
```
$ app sync
Syncing tasks... [===>    ] 45% (9/20)
```

**Using libraries:**
- Python: `tqdm`, `rich`
- Node: `cli-progress`, `ora`
- Go: `go-isatty` + custom

---

## Dangerous Operations

### Require Confirmation

**Destructive actions should:**
1. Warn about consequences
2. Require explicit confirmation
3. Provide dry-run option

**Good:**
```
$ app delete-all
This will delete all 47 tasks. This cannot be undone.
Continue? (y/N):
```

**Better:**
```
$ app delete-all
Warning: This will delete all 47 tasks.

Type 'delete all tasks' to confirm:
```

**Best:**
```
$ app delete-all --dry-run
Would delete 47 tasks:
  - Buy milk
  - Finish report
  - ...

Run without --dry-run to execute.
```

---

## Output Formatting

### Human-Readable by Default

**Good:**
```
$ app list
ID  Title           Status      Due
1   Buy milk        Incomplete  Today
2   Finish report   Incomplete  Tomorrow
3   Review PR       Complete    -
```

**Bad (CSV by default):**
```
$ app list
1,Buy milk,incomplete,2024-01-15
2,Finish report,incomplete,2024-01-16
3,Review PR,complete,
```

### Machine-Readable as Option

**Provide JSON/CSV for scripting:**

```
$ app list --format json
[
  {"id": 1, "title": "Buy milk", "status": "incomplete", "due": "2024-01-15"},
  {"id": 2, "title": "Finish report", "status": "incomplete", "due": "2024-01-16"}
]

$ app list --format csv
id,title,status,due
1,Buy milk,incomplete,2024-01-15
2,Finish report,incomplete,2024-01-16
```

---

## Performance and Responsiveness

### Instant Feedback (<100ms)

**For simple operations:**
- Adding a task
- Listing items
- Deleting items

**If operation takes >2 seconds:**
- Show progress indicator
- Allow cancellation (Ctrl+C)
- Provide ETA if possible

### Async Operations

**For truly long operations:**

```
$ app sync --async
Sync started in background (Job ID: abc123)
Check status: app jobs status abc123
```

---

## Color and Styling

### Use Color Meaningfully

**Good:**
- ✓ (green) for success
- ✗ (red) for errors
- ⚠ (yellow) for warnings
- ℹ (blue) for info

**Bad:**
- Random colors for decoration
- Color as the only indicator (accessibility)

### Respect NO_COLOR

**Always check environment:**

```python
import os

def should_use_color():
    return "NO_COLOR" not in os.environ and sys.stdout.isatty()
```

---

## Summary Checklist

Use this checklist when designing or evaluating a CLI:

### Commands
- [ ] Natural language verbs (add, list, delete)
- [ ] Consistent naming pattern (verb-noun or noun-verb)
- [ ] Standard abbreviations available (ls, rm)

### Arguments
- [ ] Positional for required inputs
- [ ] Flags for optional inputs
- [ ] Boolean flags don't require values

### Help
- [ ] Global `--help` works
- [ ] Command-specific `--help` works
- [ ] Examples included in help

### Defaults
- [ ] Zero-config first run succeeds
- [ ] Sensible defaults for 80% of users
- [ ] Progressive configuration available

### Errors
- [ ] Clear error messages (what, why, how to fix)
- [ ] Typo suggestions ("did you mean?")
- [ ] Actionable guidance

### Feedback
- [ ] Immediate confirmation for actions
- [ ] Progress indicators for slow operations
- [ ] Meaningful use of color/icons

### Safety
- [ ] Destructive operations require confirmation
- [ ] Dry-run option available
- [ ] Clear warnings before data loss
