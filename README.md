# ♠️ Klondike Spec CLI

> **The CLI that built itself** — A tool for managing AI agent workflows, created through the very methodology it implements.

[![PyPI version](https://badge.fury.io/py/klondike-spec-cli.svg)](https://badge.fury.io/py/klondike-spec-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/ThomasRohde/klondike-spec-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/ThomasRohde/klondike-spec-cli/actions)
[![Coverage](https://img.shields.io/badge/coverage-74%25-green.svg)](https://github.com/ThomasRohde/klondike-spec-cli)

---

## 🌟 The Story: When AI Builds Its Own Tools

**What happens when you ask an AI coding agent to build a tool for managing AI coding agents?**

You get Klondike Spec CLI — a project that went from concept to **100% feature completion** in just 4 coding sessions, with the AI agent using the very methodology and artifacts the tool was designed to manage.

### The Challenge

Modern AI coding agents like GitHub Copilot are powerful, but they face a fundamental limitation: **context windows reset between sessions**. Every new conversation starts fresh, losing the accumulated knowledge, decisions, and progress from previous work.

[Anthropic's research on effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) highlighted this challenge and inspired a solution: structured artifacts that bridge context windows.

### The Solution: Klondike Spec

The **Klondike Spec** framework provides:
- 📋 A **feature registry** that prevents "victory declarations" (agents claiming completion prematurely)
- 📝 A **progress log** for session-to-session handoffs
- ✅ **Verification evidence** requirements before features can be marked complete
- 🔄 **Structured workflows** that guide agents through complex, multi-session projects

> **🐍 Python-First**: Klondike Spec is currently optimized for Python development workflows, with built-in support for `uv`, `pytest`, `ruff`, and modern Python tooling. The instructions and CI/CD patterns assume a Python project structure. Contributions to support other ecosystems are welcome!

### The Meta-Journey

This CLI tool was built by an AI agent **following the Klondike Spec methodology** — tracking its own features, managing its own sessions, and providing verification evidence for each completed feature. The dog ate its own dog food, and it was delicious.

**40 features. 7 sessions. 142 tests. 100% verified.**

---

## ⚡ Built with Pith: Agent-Native CLI Design

Klondike Spec CLI is powered by [**Pith**](https://github.com/ThomasRohde/pith) — a revolutionary CLI framework designed specifically for AI agents.

Unlike traditional CLI frameworks that prioritize human interaction patterns, Pith implements **progressive discovery**:

```
Tier 1: pith → Overview of all commands
Tier 2: command → Synopsis and usage  
Tier 3: command --help → Full documentation
```

AI agents can efficiently navigate the CLI surface, discovering exactly what they need without overwhelming context. Pith also supports:

- 🎯 **Semantic intents** — Commands can be invoked by meaning, not just exact syntax
- 📊 **Structured output** — JSON mode for programmatic integration
- 🧠 **Schema export** — Full command structure for AI tooling

---

## 🤖 Multi-Agent Support

Klondike Spec CLI supports multiple AI coding agents with a pluggable adapter system.

### Supported Agents

| Agent | Flag | Templates Created |
|-------|------|-------------------|
| **GitHub Copilot** (default) | `--agent copilot` | `.github/` directory with instructions, prompts, templates |
| **Claude Code** | `--agent claude` | `CLAUDE.md` at root, `.claude/` with settings and commands |
| **Both** | `--agent all` | All templates for both agents |

### Initialize with Your Preferred Agent

```bash
# Default: GitHub Copilot
klondike init my-project

# Claude Code
klondike init my-project --agent claude

# Both agents
klondike init my-project --agent all

# Add Claude to existing Copilot project
klondike upgrade --agent claude
```

### Claude Code Integration

When using `--agent claude`, klondike creates:

```
your-project/
├── CLAUDE.md              # Main instructions file (read by Claude Code)
└── .claude/
    ├── settings.json      # Permission presets for klondike commands
    └── commands/          # Custom slash commands
        ├── session-start.md
        ├── session-end.md
        ├── verify-feature.md
        ├── progress-report.md
        ├── add-features.md
        └── recover-from-failure.md
```

Use the slash commands in Claude Code by typing `/project:command-name`.

---

## 🌳 Isolated Worktree Sessions

One of Klondike's most powerful features is the ability to run AI agents in **isolated git worktrees**. This provides a safe sandbox where agents can make changes without affecting your main project until you're ready.

### Why Worktrees?

- 🔒 **Isolation** — Changes are made in a separate directory, protecting your main branch
- 🧪 **Experimentation** — Let the agent try risky changes without fear
- 🔀 **Parallel work** — Run multiple agent sessions simultaneously on different features
- ↩️ **Easy rollback** — Just delete the worktree if things go wrong

### Worktree Commands

```bash
# Start Copilot in an isolated worktree
klondike copilot start --worktree

# Focus on a specific feature (creates branch like klondike/f001-abc123)
klondike copilot start -w --feature F001

# Custom session name
klondike copilot start -w --name "refactor-auth"

# Auto-cleanup worktree when session ends
klondike copilot start -w --cleanup

# Apply changes back to main project after session (auto-cleans up)
klondike copilot start -w --apply

# Force cleanup worktrees with uncommitted changes
klondike copilot cleanup --force

# List all active worktree sessions
klondike copilot list
```

### Worktree Directory Structure

Worktrees are created in a centralized location outside your project:

```
~/klondike-worktrees/
└── my-project/
    ├── .klondike-project          # Marker linking to original project
    ├── f001-abc123/               # Worktree for feature F001
    │   └── <full project copy>
    └── refactor-auth-def456/      # Named worktree session
        └── <full project copy>
```

The agent works in the worktree with a dedicated branch (`klondike/f001-abc123`), commits freely, and when done you can:
- Apply the changes with `--apply` (automatically cleans up the worktree)
- Cherry-pick specific commits
- Merge the branch manually
- Or just delete it with `klondike copilot cleanup --force`

> **Note**: When using `--apply`, klondike automatically excludes `.klondike/` state files from the diff, so only your code changes are applied. The klondike state in the main project remains authoritative.

---

## 🚀 Installation

### Global Installation (Recommended)

Install `klondike` as a globally available command using [uv](https://github.com/astral-sh/uv) or [pipx](https://pipx.pypa.io/):

```bash
# Using uv (fastest)
uv tool install klondike-spec-cli

# Using pipx
pipx install klondike-spec-cli
```

This makes the `klondike` command available system-wide, isolated from your project dependencies.

### Project Dependency

Add to your project's dependencies:

```bash
# Using uv
uv add klondike-spec-cli

# Using pip
pip install klondike-spec-cli
```

---

## 🎯 Quick Start

### Initialize Your Project

```bash
# Create .klondike directory and .github templates
klondike init my-awesome-project

# Include a link to your PRD for agent context
klondike init my-awesome-project --prd ./docs/prd.md

# Skip .github scaffolding if you already have it
klondike init my-awesome-project --skip-github

# See where you stand
klondike status
```

```
📊 Project: my-awesome-project v0.1.0
   Completion: 0.0%

Progress: [░░░░░░░░░░░░░░░░░░░░] 0.0%

  ⏳     Not Started         0

🎯 Ready to add features!
```

### Define Your Features

```bash
# Add features with acceptance criteria
klondike feature add -d "User authentication" -c core -p 1 \
  --criteria "Login form works,Password validation,Session management"

klondike feature add -d "Dashboard UI" -c ui -p 2 \
  --criteria "Responsive layout,Data visualization,Real-time updates"

# See your feature backlog
klondike feature list
```

### Work Through Features

```bash
# Start a coding session
klondike session start --focus "F001 - User authentication"

# Mark what you're working on
klondike feature start F001

# When complete with evidence
klondike feature verify F001 --evidence "All tests pass, demo video recorded"

# End the session
klondike session end --summary "Auth complete" --completed "Login,Logout,Sessions"
```

### Track Progress Across Sessions

```bash
# Check overall status (includes git info!)
klondike status
```

```
📊 Project: my-awesome-project v0.1.0
   Completion: 50.0%

Progress: [██████████░░░░░░░░░░] 50.0%

  ✅     Verified            1
  ⏳     Not Started         1

📅 Last Session: #1 (2025-12-07)
   Focus: F001 - User authentication

📂 Git Status: ✅ Clean (branch: main)
Recent commits:
  abc123 2025-12-07 feat(auth): implement user login

🎯 Next Priority Features:
    ⏳ Not started  F002: Dashboard UI
```

---

## 📚 Complete Command Reference

### Project Commands

| Command | Description |
|---------|-------------|
| `klondike init [name]` | Initialize .klondike directory and agent templates |
| `klondike init --agent <name>` | Select agent: `copilot` (default), `claude`, or `all` |
| `klondike init --prd <path>` | Initialize with PRD link for agent context |
| `klondike init --skip-github` | Initialize without agent template scaffolding |
| `klondike init --upgrade` | Upgrade templates while preserving user data |
| `klondike init --force` | Wipe and reinitialize (requires confirmation) |
| `klondike upgrade` | Alias for `init --upgrade` - refresh templates |
| `klondike status` | Show project status, git info, and next priorities |
| `klondike validate` | Check artifact integrity and consistency |
| `klondike config` | View or set project configuration |
| `klondike progress` | Regenerate agent-progress.md from JSON |
| `klondike report` | Generate detailed status report |
| `klondike release [version]` | Automate version bumping and release tagging |

### Feature Management

| Command | Description |
|---------|-------------|
| `klondike feature add` | Add a new feature with description and criteria |
| `klondike feature list` | List features with optional status filter |
| `klondike feature show <id>` | Display full feature details |
| `klondike feature start <id>` | Mark feature as in-progress |
| `klondike feature verify <id>` | Mark as verified with evidence |
| `klondike feature block <id>` | Mark as blocked with reason |
| `klondike feature edit <id>` | Edit notes, criteria, priority |

### Session Management

| Command | Description |
|---------|-------------|
| `klondike session start` | Begin session (validates artifacts, shows status) |
| `klondike session end` | End session with summary and handoff notes |

### AI Agent Integration

| Command | Description |
|---------|-------------|
| `klondike copilot start` | Launch GitHub Copilot CLI with klondike context |
| `klondike copilot start --worktree` | Launch Copilot in an isolated git worktree |
| `klondike copilot start -w --feature F001` | Worktree session focused on a specific feature |
| `klondike copilot list` | List active worktree sessions |
| `klondike copilot cleanup` | Remove all worktree sessions |
| `klondike mcp serve` | Start MCP server for AI agent integration |
| `klondike mcp install` | Generate MCP server config for VS Code |
| `klondike mcp config` | Output MCP configuration JSON |

### Web UI

| Command | Description |
|---------|-------------|
| `klondike serve` | Start web UI for project management |
| `klondike serve --port 3000` | Use custom port |
| `klondike serve --host 0.0.0.0` | Allow external connections |
| `klondike serve --open` | Auto-launch browser |

### Push Notifications

Klondike supports push notifications via [ntfy.sh](https://ntfy.sh) to alert you when important events occur during agent sessions.

```bash
# Configure in .klondike/config.yaml
ntfy:
  channel: my-project-alerts    # Your unique topic/channel
  server: https://ntfy.sh       # Optional: custom ntfy server
  token: tk_your_token          # Optional: auth token for private topics
  events:
    session_start: true         # Notify on session start
    session_end: true           # Notify on session end
    feature_verified: true      # Notify when features verified
    feature_blocked: true       # Notify when features blocked
    errors: true                # Notify on errors
```

**Subscribe to receive notifications:**
1. Install the [ntfy mobile app](https://ntfy.sh) or visit `https://ntfy.sh/my-project-alerts` in a browser
2. Subscribe to your chosen channel name
3. Run `klondike session start` to test — you'll get a notification! 🔔

See [docs/ntfy-config-example.md](docs/ntfy-config-example.md) for detailed setup instructions.

### Import/Export

| Command | Description |
|---------|-------------|
| `klondike import-features <file>` | Import features from YAML/JSON |
| `klondike export-features <file>` | Export features to YAML/JSON |

### Shell Completion

```bash
# Bash
klondike completion bash >> ~/.bashrc

# Zsh  
klondike completion zsh > ~/.zsh/completions/_klondike

# PowerShell
klondike completion powershell >> $PROFILE
```

---

## 📁 Project Structure

After running `klondike init`, your project will have:

### With GitHub Copilot (default)

```
your-project/
├── .klondike/
│   ├── features.json         # 📋 Feature registry (source of truth)
│   ├── agent-progress.json   # 📝 Session log and handoffs
│   └── config.yaml           # ⚙️ CLI configuration
├── agent-progress.md         # 📖 Generated human-readable progress
└── .github/
    ├── copilot-instructions.md  # 🤖 Agent behavior rules
    ├── instructions/            # 📚 Workflow instruction files
    ├── prompts/                 # 💬 Reusable prompt templates
    └── templates/               # 📐 Init scripts and schemas
```

### With Claude Code (`--agent claude`)

```
your-project/
├── .klondike/                # Same as above
├── agent-progress.md
├── CLAUDE.md                 # 🤖 Main Claude instructions
└── .claude/
    ├── settings.json         # ⚙️ Permission presets
    └── commands/             # 💬 Custom slash commands
```

### With Both (`--agent all`)

Both `.github/` and `.claude/` + `CLAUDE.md` are created.

> **Tip**: Use `--skip-github` to skip agent template creation entirely.

---

## 🔧 Configuration

`.klondike/config.yaml`:

```yaml
# Default category for new features
default_category: core

# Default priority (1=critical, 5=nice-to-have)
default_priority: 2

# Who verifies features
verified_by: coding-agent

# Where to generate the markdown progress file
progress_output_path: agent-progress.md

# Auto-regenerate markdown on changes
auto_regenerate_progress: true

# Link to PRD document for agent context (set via --prd or config command)
# prd_source: ./docs/prd.md
```

### Managing Configuration

```bash
# View all configuration
klondike config

# View specific setting
klondike config prd_source

# Set PRD source
klondike config prd_source --set ./docs/requirements.md

# Clear PRD source
klondike config prd_source --set null
```

When `prd_source` is set, the PRD link appears prominently in `agent-progress.md`, ensuring all future coding sessions have access to the original requirements.

---

## 🤝 Integration with Klondike Spec Framework

This CLI is designed to work seamlessly with the [**Klondike Spec**](https://github.com/ThomasRohde/klondike-spec) prompting framework for GitHub Copilot.

The framework provides:
- 📜 **Copilot instructions** that embed agent behavior rules
- 🎬 **Slash commands** (`/session-start`, `/session-end`, `/verify-feature`)
- 📐 **Templates** for consistent project structure

**The CLI handles artifact manipulation. The framework guides agent behavior.**

Together, they enable sophisticated multi-session agent workflows that maintain coherence across context window resets.

---

## 🧪 Development

```bash
# Clone and setup
git clone https://github.com/ThomasRohde/klondike-spec-cli.git
cd klondike-spec-cli
uv sync

# Run tests (167 tests)
uv run pytest -v

# Lint and type check
uv run ruff check .
uv run mypy src

# Build web frontend (required before building package)
cd klondike-web
npm install
npm run build
cd ..

# Build Python package with hatchling
uv run --with build python -m build

# Test locally before publishing
uv tool install --force dist/klondike_spec_cli-*.whl
klondike serve --open
```

### Publishing to PyPI

The project uses an automated release workflow:

```bash
# Publish a new version (runs tests, builds web UI, creates tag)
.\scripts\publish.ps1 -Bump patch    # 1.0.0 -> 1.0.1
.\scripts\publish.ps1 -Bump minor    # 1.0.0 -> 1.1.0
.\scripts\publish.ps1 -Bump major    # 1.0.0 -> 2.0.0

# Dry run to preview
.\scripts\publish.ps1 -Bump patch -DryRun

# Skip tests for hotfixes (not recommended)
.\scripts\publish.ps1 -Bump patch -SkipTests
```

The script:
1. ✅ Runs tests
2. 🏗️ Builds web frontend (`klondike-web`)
3. 📦 Commits changes
4. 🏷️ Creates and pushes git tag
5. 🚀 GitHub Actions builds package and publishes to PyPI

Once the tag is pushed, GitHub Actions automatically:
- Builds the web frontend
- Creates the Python wheel with bundled assets
- Publishes to PyPI using trusted publishing

Users can then install/upgrade:
```bash
uv tool install klondike-spec-cli
uv tool upgrade klondike-spec-cli
```

### Project Stats

- **40+ features** — all verified with evidence
- **167 tests** — comprehensive coverage
- **7 sessions** — iterative development
- **4500+ lines** of well-structured Python

---

## 🎴 Why "Klondike"?

Like the classic card game, building complex software with AI agents requires **patience, strategy, and careful arrangement** of moving pieces. You can't just pile cards randomly — you need structure, rules, and a clear view of your progress.

Klondike Spec provides that structure. The CLI gives you the tools to maintain it.

---

## 📜 License

MIT — See [LICENSE](LICENSE) for details.

---

## 🔗 Related Projects

- [**Klondike Spec**](https://github.com/ThomasRohde/klondike-spec) — The prompting framework for GitHub Copilot
- [**Pith**](https://github.com/ThomasRohde/pith) — Agent-native CLI framework with progressive discovery

---

<div align="center">

**Built with 🤖 by AI, for AI, verified by humans**

*"The best way to predict the future is to build the tools that build the future."*

</div>
