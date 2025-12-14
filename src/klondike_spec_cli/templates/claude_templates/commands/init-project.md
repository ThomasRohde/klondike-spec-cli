Initialize a new project with Klondike Spec agent infrastructure

# Goal

Set up the **Klondike Spec agent infrastructure** for a new project, using the `klondike` CLI to create all artifacts needed for effective multi-context-window agent workflows.

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

### 2. Create Feature Registry with Klondike CLI

Use the klondike CLI to initialize the project:

```bash
klondike init <project-name>
```

This creates the `.klondike/` directory with:
- `features.json` - Feature registry
- `agent-progress.json` - Session tracking data
- `config.yaml` - Project configuration

Then add features using the CLI:

```bash
klondike feature add "Short description" \
  --category core \
  --priority 1 \
  --criteria "Criterion 1,Criterion 2,Criterion 3" \
  --notes "Implementation: <approach>. Edge cases: <cases>. Dependencies: <deps>. Gotchas: <pitfalls>."
```

> **IMPORTANT**: Always use `--notes` to provide implementation guidance.
> A weaker agent will implement these features—give them the context they need to succeed.

Generate **at least 20 features** covering:
- Core functionality
- Error handling
- User experience
- Testing infrastructure
- Documentation
- Deployment readiness

Verify the setup with:

```bash
klondike status  # Shows project overview
klondike feature list  # Lists all features
```

### 3. Progress File (Auto-Generated)

The klondike CLI automatically generates `agent-progress.md` at project root from the data in `.klondike/agent-progress.json`. This markdown file is regenerated whenever you run klondike commands.

To manually regenerate the progress file:

```bash
klondike progress  # Displays and regenerates agent-progress.md
```

### 4. Create Init Script

Create init scripts that start the dev server **in the background** so the agent doesn't stall waiting for the server process.

**For Unix (`init.sh`)**:
```bash
#!/bin/bash
set -e

DEV_PORT=3000  # Adjust for your project

echo "Initializing development environment..."

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
        echo "Server ready on port $DEV_PORT (PID: $DEV_PID)"
        exit 0
    fi
    sleep 1
    ATTEMPT=$((ATTEMPT + 1))
done

echo "Server failed to start"
exit 1
```

**For Windows (`init.ps1`)**:
```powershell
$ErrorActionPreference = "Stop"

$DEV_PORT = 3000  # Adjust for your project

Write-Host "Initializing development environment..." -ForegroundColor Cyan

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
        Write-Host "Server ready on port $DEV_PORT (Job ID: $($devJob.Id))" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Server failed to start" -ForegroundColor Red
exit 1
```

### 5. Initialize Git Repository

```bash
git init
git add .
git commit -m "feat: initialize project with Klondike Spec infrastructure

- Created .klondike/ with features.json and agent-progress.json
- Generated agent-progress.md for session handoffs
- Set up init scripts for reproducible environment
- Configured for multi-context-window agent workflow"
```

## Output Format

Provide:
1. **Summary** of created files (in `.klondike/` directory)
2. **Feature count** breakdown by category (use `klondike feature list`)
3. **Next steps** for the first coding agent session
4. **Commands** to verify setup:
   - `klondike status` - Project overview
   - `klondike validate` - Artifact integrity check
   - `klondike feature list` - All features

## IMPORTANT: Scope Boundary

**STOP after completing the above steps.** This command is for scaffolding only.

- Run `klondike init`, add features, create init scripts, git commit
- Set up basic project structure (package.json, tsconfig, etc.)
- Do NOT start implementing features from the feature registry
- Do NOT write application code beyond minimal boilerplate

The user should run `/session-start` to begin implementing features in a separate session.

> **Want to scaffold AND build in one go?** Use `/init-and-build` instead.
