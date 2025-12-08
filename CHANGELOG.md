# Changelog

All notable changes to **Klondike Spec CLI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.9] - 2025-12-08

### 🐛 Fixed

- Template extraction no longer copies `__init__.py` files to user's `.github` directory
- Fixed filtering in `_copy_traversable_to_path`, `extract_github_templates`, and `get_github_templates_list`

---

## [0.2.8] - 2025-12-08

### ✨ Added

- Added `init-project.prompt.md` and `init-and-build.prompt.md` to templates
- `klondike init` now creates essential project initialization prompts in `.github/prompts/`

---

## [0.2.7] - 2025-12-08

### 🐛 Fixed

- MCP `install` now creates `.vscode/mcp.json` in workspace (not global Copilot storage)
- MCP install uses correct VS Code format with `servers` key (not `mcpServers`)
- MCP install adds `type: stdio` as required by VS Code MCP support
- MCP stdio mode no longer writes status messages to stdout (was corrupting protocol)
- Fixed UnicodeEncodeError from emojis in Windows stdio mode

### ✨ Added

- `generate_vscode_mcp_config()` function for portable VS Code MCP configuration

---

## [0.2.6] - 2025-12-08

### 🐛 Fixed

- Priority is now always cast to int for consistency

---

## [0.2.0] - 2025-12-08

### ✨ Added

#### MCP Server Support
- `klondike mcp serve` - Run MCP server for AI agent integration (stdio or streamable-http transport)
- `klondike mcp install` - Generate `.vscode/mcp.json` configuration for VS Code workspace
- `klondike mcp config` - Output MCP configuration to stdout or file
- MCP tools exposed: `get_features`, `get_feature`, `start_feature`, `verify_feature`, `block_feature`, `get_status`, `start_session`, `end_session`, `validate_artifacts`

#### GitHub Templates Scaffolding
- `klondike init` now creates `.github/` directory with Copilot instructions
- Includes `copilot-instructions.md` with agent workflow guidelines
- Includes `instructions/` with git practices, session management, and testing guides
- Includes `prompts/` with reusable prompt templates for common workflows
- Includes `templates/` with init scripts and JSON schemas
- Added `--skip-github` flag to opt out of GitHub scaffolding

#### Enhanced Feature Management
- `klondike feature add` now supports positional description argument
- Improved interactive prompts with better UX (pypith 0.1.2)
- Priority always cast to int for consistency

### 🐛 Fixed

- MCP stdio mode no longer writes status messages to stdout (was corrupting protocol)
- MCP install now uses correct VS Code format (`servers` key, not `mcpServers`)
- Fixed UnicodeEncodeError from emojis in Windows stdio mode

### 🔧 Changed

- MCP configuration now uses portable `klondike mcp serve` command when available
- Upgraded to pypith 0.1.2 for improved CLI UX

---

## [0.1.0] - 2025-12-07

### 🎉 Initial Release

**The CLI that built itself** — This release represents the complete implementation of Klondike Spec CLI, developed across 4 AI coding sessions using the very methodology the tool implements.

### ✨ Added

#### Core Commands
- `klondike init [name]` - Initialize .klondike directory with project artifacts
- `klondike status` - Display project status with progress bar, git info, and next priorities
- `klondike validate` - Check artifact integrity and consistency
- `klondike progress` - Regenerate agent-progress.md from JSON data

#### Feature Management
- `klondike feature add` - Add features with description, category, priority, and acceptance criteria
- `klondike feature list` - List features with optional status filtering and JSON output
- `klondike feature show <id>` - Display full feature details including verification evidence
- `klondike feature start <id>` - Mark a feature as in-progress
- `klondike feature verify <id>` - Mark a feature as verified with evidence
- `klondike feature block <id>` - Mark a feature as blocked with reason
- `klondike feature edit <id>` - Edit feature notes, priority, and criteria (description immutable)

#### Session Management
- `klondike session start` - Begin a coding session with focus tracking
- `klondike session end` - End session with summary, completed items, and handoff notes
- Automatic git status integration shows uncommitted changes and recent commits

#### Reporting & Export
- `klondike report` - Generate status reports in markdown, plain text, or JSON
- `klondike export-features <file>` - Export features to YAML or JSON with status filtering
- `klondike import-features <file>` - Import features from YAML or JSON with duplicate detection

#### Developer Experience
- `klondike completion <shell>` - Generate shell completion scripts for bash, zsh, and PowerShell
- Rich terminal output with colors, progress bars, and emoji icons
- JSON output mode for programmatic integration

#### Quality & Reliability
- Comprehensive input validation and sanitization
- Git integration for status tracking and commit logging
- Performance-optimized O(1) feature lookups via indexed data structures
- 98 tests with 74% code coverage

### 🔧 Technical Stack
- **Python 3.10+** with full type annotations
- **Pith** (pypith) - Agent-native CLI framework with progressive discovery
- **Rich** - Beautiful terminal formatting
- **PyYAML** - Configuration and import/export support
- **Hatchling** - Modern Python build backend

### 📖 Documentation
- Comprehensive README with story-driven narrative
- Complete command reference with examples
- GitHub Actions CI/CD for testing and PyPI publishing
- MIT License

---

## Development Journey

This project was developed in 4 AI coding sessions:

| Session | Focus | Features Added |
|---------|-------|----------------|
| 1 | Project foundation | Core models, init, status, feature CRUD |
| 2 | Session management | Session start/end, progress regeneration |
| 3 | Validation & reporting | Validate command, report generation |
| 4 | Polish & complete | Git integration, completion, import/export, performance |

**Final stats:**
- 30 features specified and verified
- 98 tests passing
- 74% code coverage
- 1600+ lines of Python

---

## The Meta-Achievement

> This CLI was built by an AI agent following the Klondike Spec methodology — tracking its own features, managing its own sessions, and providing verification evidence for each completed feature.

*Built with 🤖 by AI, for AI, verified by humans*

[0.1.0]: https://github.com/ThomasRohde/klondike-spec-cli/releases/tag/v0.1.0
