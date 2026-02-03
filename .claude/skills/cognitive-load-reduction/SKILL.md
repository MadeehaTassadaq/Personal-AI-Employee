---
name: cognitive-load-reduction
description: Evaluate and improve CLI/console applications for ease of use and reduced cognitive load. Use when analyzing command-line tools, console applications, or terminal interfaces to assess whether new users can succeed quickly (60-second test), whether command names are intuitive, whether defaults are sensible, and to provide concrete recommendations for UX improvements. Triggers include requests to evaluate, review, improve, or assess CLI usability, user experience, learnability, or cognitive load.
---

# Cognitive Load Reduction

## Overview

This skill helps evaluate and improve command-line interfaces (CLIs) and console applications by measuring cognitive load and identifying UX friction points. Use it to assess whether users can achieve success quickly, understand commands intuitively, and work with sensible defaults.

## Core Evaluation Framework

Every CLI evaluation should assess these five dimensions:

### 1. Time-to-First-Success (60-Second Test)
**Goal:** New users accomplish their first meaningful task within 60 seconds

**Quick Check:**
- Launch the app without arguments
- Can the user discover what to do next?
- Does the first obvious command work?
- Is success feedback clear?

**Red Flags:**
- Requires reading documentation before first use
- No guidance when launched without arguments
- First command attempt fails
- Success happens silently

### 2. Command Intuitiveness
**Goal:** Command names match user mental models

**Quick Check:**
- Are verbs natural? (add, list, delete vs create, query, remove)
- Is naming consistent? (all verb-noun OR all noun-verb)
- Would a new user guess the right command?

**Red Flags:**
- Technical jargon (serialize, flush, daemon)
- Inconsistent patterns (add-user, create_task, new-project)
- Non-standard abbreviations (lst, rmv, upd)

### 3. Sensible Defaults
**Goal:** Works well without configuration for 80% of users

**Quick Check:**
- Does zero-config first run succeed?
- Are defaults appropriate for common use cases?
- Can user defer advanced configuration?

**Red Flags:**
- Requires config file before first run
- Errors on missing optional settings
- Forces premature decisions

### 4. Error Recovery
**Goal:** Users can understand and recover from errors

**Quick Check:**
- Do error messages explain what went wrong?
- Do errors suggest how to fix the problem?
- Are typos caught with suggestions?

**Red Flags:**
- Cryptic errors (ERR_INVALID_STATE)
- No recovery guidance
- No "did you mean?" for typos

### 5. Help Discoverability
**Goal:** Help is available in context without friction

**Quick Check:**
- Does `--help` work globally and per-command?
- Are examples included?
- Is output concise (fits one screen)?

**Red Flags:**
- Help output scrolls for pages
- No examples, only syntax
- Must leave terminal for help

## Evaluation Workflow

### Quick Evaluation (5 minutes)

Use this for rapid assessment:

1. **Launch test:** Run app with no arguments
   - What happens? Is it helpful?

2. **Help test:** Run `app --help`
   - Is output helpful? Are there examples?

3. **First command:** Try the most obvious command
   - Does it work? Is feedback clear?

4. **Typo test:** Make a deliberate typo
   - Is the error message helpful?

5. **Safety test:** Check if destructive actions require confirmation

**Output:** 3-5 bullet points of key issues found

### Full Evaluation (30 minutes)

For comprehensive assessment, use the evaluation template:

1. **Read the evaluation framework:** See `references/evaluation-framework.md` for detailed criteria, measurement techniques, and scoring guidelines

2. **Use the evaluation template:** Copy `assets/evaluation-template.md` and fill in each section systematically

3. **Consult best practices:** Reference `references/cli-best-practices.md` when formulating recommendations

4. **Deliver structured report:** Complete template with ratings, findings, and prioritized recommendations

## Delivering Recommendations

### Structure of Good Recommendations

Every recommendation should include:

1. **Issue:** What's wrong (specific, observable)
2. **Impact:** Why it matters (user friction, confusion, failure)
3. **Fix:** How to improve (concrete, actionable)
4. **Example:** Before/after comparison (code or output)

### Prioritization Framework

**High Priority (Block Basic Usability):**
- Zero-config doesn't work
- Primary commands fail or unclear
- No guidance on how to start
- Cryptic error messages

**Medium Priority (Cause Friction):**
- Inconsistent command naming
- Poor defaults requiring frequent overrides
- Inadequate help text
- Missing typo suggestions

**Low Priority (Polish):**
- Verbose output
- Missing advanced features
- Lack of color/icons
- Documentation gaps

## Example Evaluation

**User Request:**
"Evaluate my todo app CLI - can new users figure it out quickly?"

**Response Structure:**

```markdown
I'll evaluate your todo app's cognitive load across five dimensions.

## Quick Assessment

**Time-to-First-Success Test:**
$ todo
Error: No command specified. See 'todo --help'

❌ Issue: Launch without args shows error, not guidance
Impact: New users don't know what to try first
Fix: Show welcome message with quick start example

**Command Intuitiveness:**
Commands found: create-task, lst, rmv, show-task

❌ Issue: Inconsistent naming (create-task vs show-task)
❌ Issue: Non-standard abbreviations (lst, rmv)
Fix: Standardize to: add, list, delete, show

**Sensible Defaults:**
$ todo create-task "Buy milk"
Error: Configuration file not found

❌ Issue: Requires config before first use
Fix: Provide sensible defaults, make config optional

## Priority Recommendations

### 1. Fix Zero-Config Experience (HIGH)
[Detailed recommendation with before/after code]

### 2. Standardize Command Names (HIGH)
[Detailed recommendation with examples]

### 3. Add Welcome Guidance (MEDIUM)
[Detailed recommendation with example output]

**Overall Rating: 2/5** - Requires significant improvements before usable by new users
```

## References

### Detailed Resources

- **`references/evaluation-framework.md`** - Comprehensive evaluation criteria, measurement techniques, scoring guide, and common anti-patterns. Read when performing full evaluations.

- **`references/cli-best-practices.md`** - Industry best practices for CLI design including command naming conventions, argument design, error messages, help text, defaults, and output formatting. Reference when formulating specific recommendations.

### Template

- **`assets/evaluation-template.md`** - Structured template for full evaluation reports. Copy and fill in when conducting comprehensive assessments.

## Key Principles

1. **New users first:** Optimize for the first-time experience, not power users
2. **60-second rule:** If basic success takes longer, there's a problem
3. **Intuitive over clever:** Natural language beats brevity
4. **Fail gracefully:** Errors should teach, not frustrate
5. **Progressive disclosure:** Simple by default, powerful when needed

## When NOT to Use This Skill

This skill is for **evaluating existing CLIs** or **designing new ones**. Don't use for:
- Implementing CLI features (use general coding skills)
- Debugging CLI bugs (use general debugging)
- Writing CLI documentation (use documentation skills)
- Performance optimization (use performance skills)

Use this skill specifically when the focus is on **usability, learnability, and cognitive load**.
