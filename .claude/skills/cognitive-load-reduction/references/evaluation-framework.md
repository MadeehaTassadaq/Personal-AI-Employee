# Cognitive Load Evaluation Framework

## Core Evaluation Dimensions

### 1. Time-to-First-Success (60-Second Test)
**Goal:** Can a new user accomplish their first meaningful task within 60 seconds?

**Evaluation Checklist:**
- [ ] User can discover primary commands without documentation
- [ ] First command attempt succeeds without errors
- [ ] Success feedback is clear and immediate
- [ ] User understands what they accomplished

**Cognitive Load Factors:**
- **Discovery load:** How hard is it to find the right command?
- **Execution load:** How many steps to complete first task?
- **Feedback load:** Is success/failure immediately clear?

**Measurement Techniques:**
- Time from launch to first successful command
- Number of help invocations needed
- Number of failed attempts before success
- User self-report: "I felt successful" (yes/no)

---

### 2. Command Intuitiveness
**Goal:** Command names match user mental models and expectations

**Evaluation Checklist:**
- [ ] Commands use familiar verbs (add, list, delete, update, show)
- [ ] Command names reflect user goals, not implementation
- [ ] Related commands follow consistent patterns
- [ ] Abbreviations are obvious or avoidable

**Cognitive Load Factors:**
- **Memory load:** Must users memorize non-obvious names?
- **Recognition load:** Can users guess the right command?
- **Translation load:** Must users translate their goal into technical terms?

**Red Flags:**
- Technical jargon (sync, flush, daemon) for user-facing actions
- Inconsistent naming (add-user, create_task, new-project)
- Non-standard abbreviations (lst, rmv, upd)
- Implementation leakage (serialize, deserialize, marshal)

**Good Patterns:**
- Natural verbs: add, remove, list, show, update, create, delete
- Domain terms: task, project, user (not record, entity, object)
- Consistent structure: `<verb> <noun>` or `<noun> <verb>`

---

### 3. Sensible Defaults
**Goal:** System works well without configuration for 80% of users

**Evaluation Checklist:**
- [ ] Zero-config first run succeeds
- [ ] Default behaviors match common use cases
- [ ] Prompts guide required inputs
- [ ] User can defer/skip advanced configuration

**Cognitive Load Factors:**
- **Decision load:** How many choices must user make upfront?
- **Configuration load:** How much setup before first success?
- **Expertise load:** Does zero-config require expert knowledge?

**Red Flags:**
- Requires config file before first run
- Errors on missing optional settings
- Forces choices user doesn't understand yet
- No guidance for required inputs

**Good Patterns:**
- Immediate success with `app` or `app start`
- Interactive prompts for required values only
- Helpful defaults with override options
- Progressive disclosure of advanced features

---

### 4. Error Recovery
**Goal:** Users can recover from errors without frustration

**Evaluation Checklist:**
- [ ] Error messages explain what went wrong
- [ ] Error messages suggest how to fix it
- [ ] Typos offer "did you mean?" suggestions
- [ ] Destructive actions require confirmation

**Cognitive Load Factors:**
- **Interpretation load:** Can user understand the error?
- **Resolution load:** Does user know how to fix it?
- **Prevention load:** Could system have prevented error?

**Good Patterns:**
- "Command 'lst' not found. Did you mean 'list'?"
- "Missing required file 'config.json'. Create with: app init"
- "Are you sure you want to delete all tasks? (y/N)"

---

### 5. Help Discoverability
**Goal:** Users can get help without leaving the flow

**Evaluation Checklist:**
- [ ] `--help` works on every command
- [ ] Help shows examples, not just syntax
- [ ] Concise output fits one screen
- [ ] Context-sensitive help available

**Cognitive Load Factors:**
- **Context switching:** Must user leave terminal to get help?
- **Information density:** Is help overwhelming or helpful?
- **Example availability:** Can user copy-paste to succeed?

**Good Patterns:**
- `app --help` (global help)
- `app add --help` (command-specific help)
- Examples for common use cases
- Links to docs for deep dives

---

## Heuristic Evaluation Process

### Quick Check (5 minutes)
1. Launch app without arguments - what happens?
2. Try `--help` - is output helpful?
3. Attempt most obvious command - does it work?
4. Make deliberate typo - is error helpful?
5. Check if destructive action requires confirmation

### Full Evaluation (30 minutes)
1. **New User Simulation:**
   - Clear terminal history/config
   - Launch app with fresh eyes
   - Time to first success
   - Document confusion points

2. **Command Inventory:**
   - List all commands
   - Check naming consistency
   - Identify jargon/abbreviations
   - Verify pattern adherence

3. **Error Scenario Testing:**
   - Missing required inputs
   - Invalid values
   - Typos in command names
   - Destructive operations

4. **Default Behavior Analysis:**
   - What works with zero config?
   - What requires setup?
   - Are defaults sensible?
   - Can user defer configuration?

---

## Scoring Guide

Rate each dimension (1-5):

**5 - Excellent:** Exceeds best practices, delightful UX
**4 - Good:** Meets best practices, minor improvements possible
**3 - Adequate:** Functional but has friction points
**2 - Poor:** Major usability issues, needs rework
**1 - Failing:** Unusable, fundamental problems

**Overall Assessment:**
- **Average 4-5:** Production ready, excellent UX
- **Average 3-4:** Good but needs polish
- **Average 2-3:** Needs significant improvements
- **Average 1-2:** Requires redesign

---

## Common Anti-Patterns

### Configuration Hell
- Requires multiple config files before first run
- No helpful defaults
- Errors on missing optional settings

### Help Paralysis
- `--help` output scrolls for pages
- No examples, only syntax
- Uses technical jargon

### Command Chaos
- Inconsistent naming (add-user, create_task, new-project)
- Non-intuitive verbs (flush, sync, marshal)
- Abbreviations without full names

### Error Hostility
- Cryptic error messages ("Error: ERR_INVALID_STATE")
- No recovery suggestions
- Silent failures

### Invisible Feedback
- Commands succeed without confirmation
- No progress indicators for long operations
- Unclear state changes
