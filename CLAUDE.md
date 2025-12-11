# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Klondike Spec CLI is a Python tool for managing AI agent workflows across context window resets. It provides structured artifacts (feature registry, progress logs) that bridge sessions, preventing premature "victory declarations" and maintaining coherence in multi-session coding projects.

Built with [Pith](https://github.com/ThomasRohde/pith), an agent-native CLI framework with progressive discovery.

## Build & Development Commands

```bash
# Setup (uses uv package manager)
uv sync

# Run tests (167 tests)
uv run pytest -v

# Run single test file
uv run pytest tests/test_cli.py -v

# Run specific test
uv run pytest tests/test_cli.py::test_init_creates_directory -v

# Lint and format check
uv run ruff check src tests
uv run ruff format --check src tests

# Type check
uv run mypy src

# Build package
uv build

# Run CLI locally
uv run klondike --help
```

## Pre-Commit Verification (MANDATORY)

Before every commit, run these commands and ensure all pass:
1. `uv run ruff check src tests` - Lint check
2. `uv run ruff format --check src tests` - Format check
3. `uv run pytest` - All tests pass

## Architecture

### Source Structure (`src/klondike_spec_cli/`)

| Module | Purpose |
|--------|---------|
| `cli.py` | Main Pith application with all commands (`init`, `status`, `feature`, `session`, etc.) |
| `models.py` | Core dataclasses: `Feature`, `FeatureRegistry`, `Session`, `ProgressLog`, `Config` |
| `validation.py` | Input sanitization and validation utilities |
| `git.py` | Git operations (status, commits, tags, push) |
| `copilot.py` | GitHub Copilot CLI integration |
| `worktree.py` | Git worktree management for isolated sessions |
| `mcp_server.py` | MCP (Model Context Protocol) server for AI tool integration |
| `completion.py` | Shell completion generation |
| `formatting.py` | Rich console output formatting |
| `templates/` | Bundled template files for `klondike init` |

### Data Flow

```
.klondike/features.json  ←→  FeatureRegistry  ←→  CLI commands
.klondike/agent-progress.json  ←→  ProgressLog  ←→  agent-progress.md (auto-generated)
.klondike/config.yaml  ←→  Config
```

### Key Constants (`cli.py`)
- `KLONDIKE_DIR = ".klondike"` - Project artifacts directory
- `FEATURES_FILE = "features.json"` - Feature registry
- `PROGRESS_FILE = "agent-progress.json"` - Session log
- `CONFIG_FILE = "config.yaml"` - CLI configuration

## Klondike Workflow Rules

When working on this project or any klondike-managed project:

1. **Never manually edit** `.klondike/*.json` files - use CLI commands
2. **Use `klondike status`** to see project overview
3. **Use `klondike validate`** to check artifact integrity
4. **One feature at a time** - use `klondike feature start F00X`
5. **Verify before marking complete** - use `klondike feature verify F00X --evidence "..."`

## Versioning

Uses dynamic versioning via `hatch-vcs` - versions derived from git tags:
- On tag `v0.3.0` → version `0.3.0`
- 3 commits after tag → version `0.3.1.dev3`

## CI/CD

Automated via GitHub Actions:
- CI runs on every push (lint, format, test)
- Publish triggered after CI success on master
- Uses PyPI trusted publishing (OIDC)

## Testing Patterns

Tests are in `tests/` with pytest fixtures in individual test files. Most tests use temporary directories via `tmp_path` fixture. CLI tests invoke commands via `CliRunner` from pith/typer.
