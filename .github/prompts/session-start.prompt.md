---
name: session-start
description: "Start a new coding session with proper context gathering"
---

# Goal

Execute the **standardized startup routine** for a long-running agent session, ensuring you have full context before making any changes.

## Instructions

### 1. Orient Yourself

```bash
# Confirm working directory
pwd  # or Get-Location on Windows

# Check project structure
ls -la  # or Get-ChildItem
```

### 2. Read Progress Artifacts

**Use klondike CLI to check project status (REQUIRED):**

```bash
# Get project status and feature summary
klondike status

# List all features with their status
klondike feature list

# Validate artifact integrity
klondike validate
```

> ⚠️ **IMPORTANT**: Do NOT read `.klondike/features.json` or `agent-progress.md` directly. Always use klondike CLI commands.

**Git history** - Recent changes:
```bash
git log --oneline -15
git status
```

### 3. Start the Session

```bash
klondike session start --focus "F00X - Feature description"
```

If your project has an init script for dev server:

```bash
./init.sh  # or .\init.ps1 on Windows
```

### 4. Smoke Test

Before implementing new features, verify basic functionality:

- **For web apps**: Navigate to main page, perform core action
- **For APIs**: Hit health endpoint, test one main endpoint
- **For CLI tools**: Run help command, execute basic operation

### 5. Create Session Plan

Before starting work, create a plan with 3-6 concrete steps:

```markdown
#### Session Plan
| # | Task | Status |
|---|------|--------|
| 1 | <specific task> | in-progress |
| 2 | <specific task> | not-started |
| 3 | <specific task> | not-started |
```

### 6. Select Next Task

```bash
klondike feature start F00X
```

Based on your review:
1. If environment is broken → Fix it first
2. If there are incomplete in-progress features → Complete them
3. Otherwise → Pick highest priority feature from `klondike status`

### 7. Begin

Before making changes, state:
- Which feature you'll work on (by ID and description)
- Your approach in 2-3 sentences
- Any risks or dependencies you've identified

**Then immediately begin implementation.**
