---
name: init-project
description: "Initialize a new project with long-running agent harness infrastructure"
---

# Goal

Set up the **initializer agent infrastructure** for a new project, creating all artifacts needed for effective multi-context-window agent workflows.

## Context

Based on [Anthropic's research on long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), projects benefit from:
- A structured feature list that prevents premature completion
- A progress file for agent-to-agent handoffs
- An init script for reproducible environment startup
- Git infrastructure for tracking and reverting changes

## Instructions

### 1. Gather Project Information
- Confirm project type and name from user input
- Ask clarifying questions about:
  - Primary language/framework
  - Key features to implement (at least 5-10)
  - Testing approach (unit, integration, e2e)
  - Deployment target (if known)

### 2. Create Feature Registry (`features.json`)
Based on user requirements, generate a comprehensive feature list:

```json
{
  "projectName": "<name>",
  "version": "0.1.0",
  "features": [
    {
      "id": "F001",
      "category": "core|ui|api|testing|infrastructure",
      "priority": 1,
      "description": "Short description of the feature",
      "acceptanceCriteria": [
        "Specific testable criterion 1",
        "Specific testable criterion 2"
      ],
      "passes": false,
      "verifiedAt": null,
      "verifiedBy": null
    }
  ],
  "metadata": {
    "createdAt": "<timestamp>",
    "lastUpdated": "<timestamp>",
    "totalFeatures": 0,
    "passingFeatures": 0
  }
}
```

Generate **at least 20 features** covering:
- Core functionality
- Error handling
- User experience
- Testing infrastructure
- Documentation
- Deployment readiness

### 3. Create Progress File (`agent-progress.md`)

```markdown
# Agent Progress Log

## Project: <name>
## Started: <date>
## Current Status: Initialization

---

## Session Log

### Session 1 - Initialization
**Date**: <date>
**Agent**: Initializer

#### Completed
- Created project structure
- Generated features.json with X features
- Set up init script
- Created initial git commit

#### In Progress
- None

#### Blockers
- None

#### Next Steps
1. Begin implementing F001: <description>
2. Set up development environment
3. Run initial smoke tests

---

## Quick Reference

### Running the Project
\`\`\`bash
./init.sh  # or .\init.ps1 on Windows
\`\`\`

### Current Priority Features
| ID | Description | Status |
|----|-------------|--------|
| F001 | ... | ⏳ |
| F002 | ... | ⏳ |
| F003 | ... | ⏳ |
```

### 4. Create Init Script

Create init scripts that start the dev server **in the background** so the agent doesn't stall waiting for the server process.

**For Unix (`init.sh`)**:
```bash
#!/bin/bash
set -e

DEV_PORT=3000  # Adjust for your project

echo "🚀 Initializing development environment..."

# Kill any stale dev servers
if command -v lsof &> /dev/null; then
    STALE_PID=$(lsof -ti:$DEV_PORT 2>/dev/null || true)
    if [ -n "$STALE_PID" ]; then
        kill -9 $STALE_PID 2>/dev/null || true
    fi
fi

# Install dependencies
npm install  # or pip install -r requirements.txt, etc.

# Start dev server in BACKGROUND (critical for agent workflows)
npm run dev > .dev-server.log 2>&1 &
DEV_PID=$!
echo $DEV_PID > .dev-server.pid

# Wait for server to be ready
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -o /dev/null "http://localhost:$DEV_PORT" 2>/dev/null; then
        echo "✅ Server ready on port $DEV_PORT (PID: $DEV_PID)"
        exit 0
    fi
    sleep 1
    ATTEMPT=$((ATTEMPT + 1))
done

echo "❌ Server failed to start"
exit 1
```

**For Windows (`init.ps1`)**:
```powershell
$ErrorActionPreference = "Stop"

$DEV_PORT = 3000  # Adjust for your project

Write-Host "🚀 Initializing development environment..." -ForegroundColor Cyan

# Kill any stale dev servers
$staleProcesses = Get-NetTCPConnection -LocalPort $DEV_PORT -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
if ($staleProcesses) {
    foreach ($pid in $staleProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

# Install dependencies
npm install  # or pip install -r requirements.txt, etc.

# Start dev server in BACKGROUND using Start-Job (critical for agent workflows)
$devJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run dev 2>&1
}

# Wait for server to be ready
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 1
    $attempt++
    $conn = Test-NetConnection -ComputerName localhost -Port $DEV_PORT -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) {
        Write-Host "✅ Server ready on port $DEV_PORT (Job ID: $($devJob.Id))" -ForegroundColor Green
        exit 0
    }
}

Write-Host "❌ Server failed to start" -ForegroundColor Red
exit 1
```

**Key points:**
- Server runs in background (`&` in bash, `Start-Job` in PowerShell)
- Output redirected to log file for later debugging
- PID saved for cleanup
- Health check waits for server to be ready
- Script exits after health check passes (doesn't block on server)

### 5. Initialize Git Repository

```bash
git init
git add .
git commit -m "feat: initialize project with agent harness infrastructure

- Created features.json with comprehensive feature list
- Added agent-progress.md for session handoffs
- Set up init scripts for reproducible environment
- Configured for multi-context-window agent workflow"
```

### 6. Create VS Code Settings

Ensure `.vscode/settings.json` includes:
```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "chat.promptFiles": true
}
```

## Output Format

Provide:
1. **Summary** of created files
2. **Feature count** breakdown by category
3. **Next steps** for the first coding agent session
4. **Commands** to verify setup

## IMPORTANT: Scope Boundary

**STOP after completing the above steps.** This prompt is for scaffolding only.

- ✅ Create `features.json`, `agent-progress.md`, init scripts, git commit
- ✅ Set up basic project structure (package.json, tsconfig, etc.)
- ❌ Do NOT start implementing features from `features.json`
- ❌ Do NOT write application code beyond minimal boilerplate

The user should run `/session-start` to begin implementing features in a separate session.

> **Want to scaffold AND build in one go?** Use `/init-and-build` instead.
