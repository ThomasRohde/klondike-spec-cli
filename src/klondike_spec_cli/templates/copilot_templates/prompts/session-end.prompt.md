---
name: session-end
description: "End a coding session with proper documentation and clean state"
---

# Goal

Execute the **standardized shutdown routine** for a long-running agent session, ensuring the codebase is left in a clean, well-documented state for the next session.

## Instructions

### 1. Verify Clean State

**Step 1: Detect stack and available commands**

Read project configuration files to find build, test, and lint commands.

**Step 2: Run and record each command**

```bash
# Check for uncommitted changes
git status

# Run detected commands
# Example for Python:
uv run ruff check src tests
uv run pytest

# Example for Node.js:
npm run build
CI=true npm test
npm run lint
```

**Step 3: Record results before any commit**

```markdown
#### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| <build command> | 0 | ✅ |
| <test command> | 0 | ✅ N tests passed |
| <lint command> | 0 | ✅ |
```

### 2. Commit Outstanding Work

All changes should be committed with descriptive messages:

```bash
git add -A
git commit -m "<type>(<scope>): <description>"
```

### 3. Verify Feature Completion

For any features you worked on:

```bash
# Verify a feature with evidence
klondike feature verify F00X --evidence "test-results/F00X-screenshot.png"

# Or block a feature if incomplete
klondike feature block F00X --reason "Waiting for API specification"
```

### 4. End the Session

```bash
klondike session end \
  --summary "Completed login form implementation" \
  --completed "Added login form,Added validation" \
  --next "Add password reset,Implement session management"
```

### 5. Final Verification

```bash
# Ensure everything is committed
git status  # Should show "nothing to commit, working tree clean"
```

## Output Format

```markdown
## Session End Report

**Session Duration**: <time>
**Commits Made**: <count>

### Pre-Commit Verification
| Command | Exit Code | Notes |
|---------|-----------|-------|
| <command> | 0 | ✅ |

### Accomplishments
| Feature | Status | Evidence |
|---------|--------|----------|
| F00X | ✅ verified | [screenshot](test-results/F00X.png) |
| F00Y | 🔄 in-progress | 80% done |

### State Verification
- [x] All changes committed
- [x] Pre-commit checks passed
- [x] Progress file updated

### Handoff to Next Session
> <2-3 sentence summary of where things stand and what to do next>
```
