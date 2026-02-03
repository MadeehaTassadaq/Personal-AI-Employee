# Cognitive Load Evaluation Report

**Application:** [App Name]
**Version:** [Version Number]
**Evaluator:** [Name/AI]
**Date:** [YYYY-MM-DD]
**Evaluation Duration:** [Minutes]

---

## Executive Summary

**Overall Rating:** [X/5]

**Key Findings:**
- [Finding 1]
- [Finding 2]
- [Finding 3]

**Priority Recommendations:**
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

---

## 1. Time-to-First-Success (60-Second Test)

**Rating:** [X/5]

### Test Scenario
**User Goal:** [What a new user would naturally try to do first]

**Test Process:**
- Launch command: `[command]`
- Expected outcome: [What should happen]
- Actual outcome: [What did happen]
- Time elapsed: [X seconds]

### Results
- [ ] User discovered primary commands without documentation
- [ ] First command attempt succeeded without errors
- [ ] Success feedback was clear and immediate
- [ ] User understood what they accomplished

**Issues Found:**
- [Issue 1]
- [Issue 2]

**Recommendations:**
- [Recommendation 1]
- [Recommendation 2]

**Example Fix:**
```
# Current behavior:
$ app
[Current output]

# Suggested behavior:
$ app
[Improved output with clear guidance]
```

---

## 2. Command Intuitiveness

**Rating:** [X/5]

### Command Inventory
| Command | Intuitiveness | Pattern Match | Issues |
|---------|---------------|---------------|--------|
| [cmd1]  | [Good/Fair/Poor] | [Yes/No] | [Issue if any] |
| [cmd2]  | [Good/Fair/Poor] | [Yes/No] | [Issue if any] |

### Evaluation Checklist
- [ ] Commands use familiar verbs
- [ ] Command names reflect user goals
- [ ] Related commands follow consistent patterns
- [ ] Abbreviations are obvious or avoidable

**Issues Found:**
- [Issue 1: e.g., "Uses technical jargon: 'serialize' instead of 'export'"]
- [Issue 2: e.g., "Inconsistent patterns: 'add task' vs 'create-project'"]

**Recommendations:**
- [Recommendation 1: e.g., "Rename 'serialize' to 'export'"]
- [Recommendation 2: e.g., "Standardize to 'add project' pattern"]

**Example Fix:**
```
# Before:
app create-task "Buy milk"
app add-project "My Project"
app lst

# After:
app add task "Buy milk"
app add project "My Project"
app list
```

---

## 3. Sensible Defaults

**Rating:** [X/5]

### Zero-Config Test
**Test Process:**
- Fresh install with no config
- Run primary command: `[command]`
- Result: [Success/Failure]

### Evaluation Checklist
- [ ] Zero-config first run succeeds
- [ ] Default behaviors match common use cases
- [ ] Prompts guide required inputs
- [ ] User can defer advanced configuration

**Issues Found:**
- [Issue 1: e.g., "Requires config.json before first run"]
- [Issue 2: e.g., "No default output format specified"]

**Recommendations:**
- [Recommendation 1: e.g., "Provide sensible defaults, make config optional"]
- [Recommendation 2: e.g., "Default to human-readable table format"]

**Example Fix:**
```python
# Before:
def load_config():
    with open('config.json') as f:  # Fails if missing
        return json.load(f)

# After:
def load_config():
    defaults = {'format': 'table', 'date_format': 'relative'}
    try:
        with open('config.json') as f:
            return {**defaults, **json.load(f)}
    except FileNotFoundError:
        return defaults
```

---

## 4. Error Recovery

**Rating:** [X/5]

### Error Scenarios Tested
| Scenario | Error Message Quality | Recovery Guidance | Rating |
|----------|----------------------|-------------------|--------|
| [Typo in command] | [Good/Fair/Poor] | [Yes/No] | [X/5] |
| [Missing argument] | [Good/Fair/Poor] | [Yes/No] | [X/5] |
| [Invalid input] | [Good/Fair/Poor] | [Yes/No] | [X/5] |

### Evaluation Checklist
- [ ] Error messages explain what went wrong
- [ ] Error messages suggest how to fix it
- [ ] Typos offer "did you mean?" suggestions
- [ ] Destructive actions require confirmation

**Issues Found:**
- [Issue 1: e.g., "Cryptic error: 'ERR_INVALID_STATE' with no explanation"]
- [Issue 2: e.g., "Typos result in 'command not found' with no suggestions"]

**Recommendations:**
- [Recommendation 1: e.g., "Add plain-English error explanations"]
- [Recommendation 2: e.g., "Implement fuzzy matching for command suggestions"]

**Example Fix:**
```
# Before:
$ app dlete task 1
Error: Command not found

# After:
$ app dlete task 1
Error: Command 'dlete' not found. Did you mean 'delete'?

Run 'app --help' to see all commands.
```

---

## 5. Help Discoverability

**Rating:** [X/5]

### Help Availability Test
| Command | Help Available | Output Quality | Examples Included |
|---------|---------------|----------------|-------------------|
| `app --help` | [Yes/No] | [Good/Fair/Poor] | [Yes/No] |
| `app [cmd] --help` | [Yes/No] | [Good/Fair/Poor] | [Yes/No] |

### Evaluation Checklist
- [ ] `--help` works on every command
- [ ] Help shows examples, not just syntax
- [ ] Concise output fits one screen
- [ ] Context-sensitive help available

**Issues Found:**
- [Issue 1: e.g., "Help text is 200 lines, overwhelming"]
- [Issue 2: e.g., "No examples provided, only syntax"]

**Recommendations:**
- [Recommendation 1: e.g., "Condense help to one screen, link to docs for details"]
- [Recommendation 2: e.g., "Add 2-3 examples per command"]

**Example Fix:**
```
# Before:
$ app add --help
Usage: app add <title>
  --due <date>       Due date
  --priority <level> Priority level
  --tags <tags>      Tags

# After:
$ app add --help
Add a new task

USAGE:
  app add <title> [options]

EXAMPLES:
  app add "Buy milk"
  app add "Finish report" --due tomorrow --priority high

OPTIONS:
  --due <date>       Due date (e.g., tomorrow, 2024-01-15)
  --priority <level> Priority: low, medium, high (default: medium)
```

---

## Detailed Findings

### Cognitive Load Hotspots

**Hotspot 1: [Area]**
- **Issue:** [Description]
- **Impact:** [High/Medium/Low]
- **Load Type:** [Discovery/Execution/Memory/Decision]
- **Fix:** [Specific recommendation]

**Hotspot 2: [Area]**
- **Issue:** [Description]
- **Impact:** [High/Medium/Low]
- **Load Type:** [Discovery/Execution/Memory/Decision]
- **Fix:** [Specific recommendation]

### Positive Patterns

**What Works Well:**
- [Positive aspect 1]
- [Positive aspect 2]
- [Positive aspect 3]

---

## Implementation Priorities

### High Priority (Do First)
These issues block basic usability:
1. [Issue 1]
2. [Issue 2]

### Medium Priority (Do Next)
These issues cause friction but aren't blockers:
1. [Issue 1]
2. [Issue 2]

### Low Priority (Nice to Have)
These are polish improvements:
1. [Issue 1]
2. [Issue 2]

---

## Before/After Comparison

### Key Interaction Flow

**Current Experience:**
```
$ [current command sequence]
[current output/behavior]
```

**Recommended Experience:**
```
$ [improved command sequence]
[improved output/behavior with clear guidance]
```

---

## Appendix: Test Transcript

**Full test session with timestamps:**

```
[00:00] $ app
[output]

[00:05] $ app --help
[output]

[00:15] $ app add "Buy milk"
[output]

... [continue with full session transcript]
```

---

## Summary Metrics

| Dimension | Score | Benchmark | Status |
|-----------|-------|-----------|--------|
| Time-to-First-Success | [X/5] | 4+ | [✓ Pass / ✗ Needs Work] |
| Command Intuitiveness | [X/5] | 4+ | [✓ Pass / ✗ Needs Work] |
| Sensible Defaults | [X/5] | 4+ | [✓ Pass / ✗ Needs Work] |
| Error Recovery | [X/5] | 3+ | [✓ Pass / ✗ Needs Work] |
| Help Discoverability | [X/5] | 4+ | [✓ Pass / ✗ Needs Work] |
| **Overall** | **[X/5]** | **4+** | **[✓ Pass / ✗ Needs Work]** |

**Recommendation:**
- **4-5:** Production ready, excellent UX
- **3-4:** Good but needs polish before wide release
- **2-3:** Requires significant improvements
- **1-2:** Needs fundamental redesign
