# Klondike CLI Command Reference

Complete reference for all klondike commands.

## CRITICAL: Command Syntax

**Klondike does NOT use --help flags:**
- ❌ `klondike --help` (wrong)
- ❌ `klondike feature --help` (wrong)
- ✅ `klondike` (shows all commands)
- ✅ `klondike feature add ...` (just run commands, they show usage on error)

**Feature IDs must be uppercase F-prefix:**
- ❌ `f001`, `1`, `feature1` (wrong)
- ✅ `F001` (correct)

## Table of Contents

- [Project Commands](#project-commands)
- [Feature Commands](#feature-commands)
- [Session Commands](#session-commands)
- [Copilot Integration](#copilot-integration)
- [Import/Export](#importexport)
- [Configuration](#configuration)

---

## Project Commands

### `klondike init`

Initialize a new klondike project.

```bash
klondike init                           # Default (Copilot)
klondike init --name my-project         # Custom name
klondike init --agent claude            # Claude Code templates
klondike init --agent all               # Both agents
klondike init --prd ./docs/prd.md       # Link PRD
klondike init --skip-github             # No agent templates
klondike init --upgrade                 # Upgrade existing
klondike init --force                   # Wipe and reinit
```

Creates:
- `.klondike/features.json` - Feature registry
- `.klondike/agent-progress.json` - Session log
- `.klondike/config.yaml` - Configuration
- `agent-progress.md` - Human-readable progress
- `.github/` or `.claude/` - Agent templates

### `klondike upgrade`

Alias for `init --upgrade`. Refreshes templates while preserving data.

```bash
klondike upgrade                        # Upgrade current agent
klondike upgrade --agent claude         # Add Claude support
klondike upgrade --agent all            # Upgrade all agents
```

### `klondike status`

Show project overview with feature counts, git status, and priorities.

```bash
klondike status                         # Text output
klondike status --json                  # JSON output
```

Output includes:
- Project name and version
- Completion percentage
- Features by status
- Last session info
- Git branch and recent commits
- Priority features

### `klondike validate`

Check artifact integrity.

```bash
klondike validate
```

Checks:
- Metadata consistency
- Feature ID format (F###)
- Duplicate IDs
- Verified features have evidence
- Sequential session numbers

### `klondike progress`

Regenerate `agent-progress.md` from JSON data.

```bash
klondike progress                       # Default location
klondike progress --output custom.md    # Custom path
```

### `klondike report`

Generate stakeholder-friendly report.

```bash
klondike report                         # Markdown output
klondike report --format plain          # Plain text
klondike report --output report.md      # Save to file
klondike report --details               # Include feature details
```

---

## Feature Commands

All feature commands use: `klondike feature <action> [args] [options]`

### `klondike feature add`

Add a new feature to the registry.

```bash
klondike feature add "User authentication" --notes "Use bcrypt, validate email format"
klondike feature add "Login form" --category core --priority 1 --notes "Bootstrap styling"
klondike feature add "API endpoint" --criteria "Returns 200,Validates input" --notes "See api.md"
```

**Key options:**
- `--notes` - **ALWAYS use this** - helps future agents understand implementation approach
- `--category` / `-c` - Feature category (defaults from config)
- `--priority` / `-p` - Priority 1-5, 1=critical (defaults from config)
- `--criteria` - Comma-separated acceptance criteria

**Notes should include:** implementation approach, edge cases, dependencies, gotchas.

### `klondike feature list`

List all features.

```bash
klondike feature list                   # All features
klondike feature list --status verified # Filter by status
klondike feature list --json            # JSON output
```

**Status values:** `not-started`, `in-progress`, `blocked`, `verified`

### `klondike feature show`

Display detailed feature information.

```bash
klondike feature show F001              # Rich output
klondike feature show F001 --json       # JSON output
```

### `klondike feature start`

Mark feature as in-progress.

```bash
klondike feature start F001
```

Sets:
- `status: "in-progress"`
- `lastWorkedOn: <timestamp>`

### `klondike feature verify`

Mark feature as verified with evidence.

```bash
klondike feature verify F001 --evidence "test-results/F001.png"
klondike feature verify F001 -e "path1.png,path2.log"
```

**Requirements before verify:**
1. All acceptance criteria tested
2. E2E testing completed (not just unit tests)
3. Evidence captured and linked

### `klondike feature block`

Mark feature as blocked.

```bash
klondike feature block F001 --reason "Waiting for API"
klondike feature block F002 -r "Dependency on F001"
```

### `klondike feature edit`

Edit existing feature.

```bash
klondike feature edit F001 --notes "Updated notes"
klondike feature edit F001 --add-criteria "New criterion"
klondike feature edit F001 --priority 2
klondike feature edit F001 --category ui
```

### `klondike feature prompt`

Generate copilot-ready prompt for a feature.

```bash
klondike feature prompt F001            # Output to console
klondike feature prompt F001 -o prompt.md
klondike feature prompt F001 --interactive  # Launch copilot
```

---

## Session Commands

All session commands use: `klondike session <action> [options]`

### `klondike session start`

Begin a new coding session.

```bash
klondike session start --focus "F001 - User login"
klondike session start -f "Authentication feature"
```

**What it does:**
1. Validates artifacts
2. Shows current status
3. Records session start
4. Updates quick reference

### `klondike session end`

End the current session.

```bash
klondike session end --summary "Completed login" --next "Implement logout"
klondike session end -s "Done" -n "Next step" --completed "Item1,Item2"
klondike session end --blockers "API issue"
klondike session end --auto-commit
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--summary` | `-s` | Session summary (required) |
| `--completed` | `-c` | Completed items (comma-separated) |
| `--blockers` | `-b` | Blockers encountered |
| `--next` | `-n` | Next steps (comma-separated) |
| `--auto-commit` | | Auto-commit changes |

---

## Copilot Integration

### `klondike copilot start`

Launch GitHub Copilot CLI with klondike context.

```bash
klondike copilot start                  # Basic launch
klondike copilot start --model gpt-4    # Specific model
klondike copilot start --resume         # Resume session
klondike copilot start -f F001          # Focus on feature
klondike copilot start -i "Custom instructions"
```

**Worktree Mode** (isolated sessions):

```bash
klondike copilot start --worktree       # Isolated worktree
klondike copilot start -w --feature F001
klondike copilot start -w --name "refactor-auth"
klondike copilot start -w --cleanup     # Auto-cleanup after
klondike copilot start -w --apply       # Apply changes back
```

### `klondike copilot list`

List active worktree sessions.

```bash
klondike copilot list
```

### `klondike copilot cleanup`

Remove worktree sessions.

```bash
klondike copilot cleanup                # Safe cleanup
klondike copilot cleanup --force        # Force (uncommitted changes)
```

---

## Import/Export

### `klondike import-features`

Import features from YAML/JSON file.

```bash
klondike import-features backlog.yaml
klondike import-features features.json --dry-run
```

**File format:**
```yaml
features:
  - description: "Feature description"
    category: core
    priority: 1
    acceptance_criteria:
      - "Criterion 1"
      - "Criterion 2"
```

### `klondike export-features`

Export features to file.

```bash
klondike export-features backup.yaml
klondike export-features features.json --status verified
klondike export-features full.yaml --all  # Include internal fields
```

---

## Configuration

### `klondike config`

View or set configuration.

```bash
klondike config                         # Show all
klondike config prd_source              # Show specific
klondike config prd_source --set ./prd.md
klondike config default_priority -s 2
```

**Config keys:**
| Key | Description | Default |
|-----|-------------|---------|
| `prd_source` | Link to PRD document | (not set) |
| `default_category` | Default feature category | core |
| `default_priority` | Default feature priority | 2 |
| `verified_by` | Verification identifier | coding-agent |
| `progress_output_path` | Progress file path | agent-progress.md |
| `auto_regenerate_progress` | Auto-update progress file | true |

---

## MCP Server

### `klondike mcp serve`

Start MCP server for AI agent integration.

```bash
klondike mcp serve                      # stdio transport
klondike mcp serve --transport streamable-http
```

### `klondike mcp install`

Install MCP configuration for VS Code.

```bash
klondike mcp install
klondike mcp install --output mcp-config.json
```

### `klondike mcp config`

Generate MCP configuration JSON.

```bash
klondike mcp config
klondike mcp config --output config.json
```

---

## Utility Commands

### `klondike version`

Show CLI version.

```bash
klondike version
klondike version --json
```

### `klondike completion`

Generate shell completions.

```bash
klondike completion bash
klondike completion zsh --output ~/.zsh/completions/_klondike
klondike completion powershell >> $PROFILE
```

### `klondike serve`

Start web UI server.

```bash
klondike serve                          # http://127.0.0.1:8000
klondike serve --port 3000
klondike serve --host 0.0.0.0           # External access
klondike serve --open                   # Auto-open browser
```

### `klondike agents generate`

Generate AGENTS.md from project state.

```bash
klondike agents generate
```
