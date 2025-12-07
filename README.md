# 🎴 Klondike Spec CLI

A CLI tool for managing [Klondike Spec](https://github.com/ThomasRohde/klondike-spec) agent workflow artifacts.

[![PyPI version](https://badge.fury.io/py/klondike-spec-cli.svg)](https://badge.fury.io/py/klondike-spec-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Klondike Spec CLI provides command-line tools for managing the structured artifacts that enable multi-context-window agent workflows:

- **Feature Registry** (`features.json`) - Track feature completion with verification evidence
- **Progress Log** (`agent-progress.json`) - Session-by-session handoff documentation
- **Generated Markdown** (`agent-progress.md`) - Human-readable progress for stakeholders

Built with [pith](https://github.com/ThomasRohde/pith) for agent-native progressive discovery.

## Installation

```bash
pip install klondike-spec-cli
```

## Quick Start

### Initialize a New Project

```bash
# Create .klondike directory with artifacts
klondike init --name my-project

# Check status
klondike status
```

### Manage Features

```bash
# Add a feature
klondike feature add --description "User authentication" --category core

# List all features
klondike feature list

# Start working on a feature
klondike feature start F001

# Verify a feature (with evidence)
klondike feature verify F001 --evidence test-results/F001-login.png

# Block a feature
klondike feature block F002 --reason "Waiting for API spec"
```

### Session Management

```bash
# Start a coding session
klondike session start --focus "F001 - User authentication"

# End session with summary
klondike session end --summary "Completed login form" --completed "Added form,Validation"
```

### Other Commands

```bash
# Validate artifact integrity
klondike validate

# Regenerate agent-progress.md
klondike progress

# View feature details
klondike feature show F001 --json
```

## Command Reference

| Command | Description |
|---------|-------------|
| `klondike init` | Initialize .klondike directory |
| `klondike status` | Show project status summary |
| `klondike feature add` | Add a new feature |
| `klondike feature list` | List features with filters |
| `klondike feature start <id>` | Mark feature as in-progress |
| `klondike feature verify <id>` | Mark feature as verified |
| `klondike feature block <id>` | Mark feature as blocked |
| `klondike feature show <id>` | Show feature details |
| `klondike session start` | Begin a new session |
| `klondike session end` | End current session |
| `klondike validate` | Validate artifact integrity |
| `klondike progress` | Regenerate agent-progress.md |

## Directory Structure

```
your-project/
├── .klondike/
│   ├── features.json         # Feature registry (primary data)
│   ├── agent-progress.json   # Progress log (JSON format)
│   └── config.yaml           # CLI configuration
└── agent-progress.md         # Generated from JSON (human-readable)
```

## Configuration

The `.klondike/config.yaml` file contains:

```yaml
# Default category for new features
default_category: core

# Default priority (1-5, 1=critical)
default_priority: 2

# Identifier for verifiedBy field
verified_by: coding-agent

# Output path for generated markdown
progress_output_path: agent-progress.md

# Auto-regenerate markdown on changes
auto_regenerate_progress: true
```

## Integration with Klondike Spec Framework

This CLI is designed to work with the [Klondike Spec](https://github.com/ThomasRohde/klondike-spec) prompting framework for GitHub Copilot. The framework provides:

- Slash commands (`/session-start`, `/session-end`, `/verify-feature`)
- Embedded instructions for agent behavior
- Templates for structured agent workflows

When used together, the CLI handles artifact manipulation while the prompts guide agent behavior.

## Development

```bash
# Clone the repository
git clone https://github.com/ThomasRohde/klondike-spec-cli.git
cd klondike-spec-cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src
```

## License

MIT - See [LICENSE](LICENSE) for details.

## Related Projects

- [Klondike Spec](https://github.com/ThomasRohde/klondike-spec) - The prompting framework
- [Pith](https://github.com/ThomasRohde/pith) - Agent-native CLI ecosystem
