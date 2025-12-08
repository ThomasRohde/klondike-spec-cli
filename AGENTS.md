# klondike-spec-cli — Agents Guide

Generated: 2025-12-08 17:35

## Workflow Overview
- Use klondike CLI to manage features and sessions
- Do not edit .klondike JSON files directly; use CLI commands
- Keep one feature in progress at a time

## Key Commands
```bash
klondike status
klondike feature list
klondike session start --focus "F00X - description"
klondike feature start F00X
```

## Configuration
- default_category: core
- default_priority: 2
- verified_by: coding-agent
- progress_output_path: agent-progress.md

## Current Priority Features
- F034: Generate AGENTS.md from klondike configuration (in-progress)
- F039: Local CI check command that detects and runs project CI checks (not-started)
- F035: Auto-delegate feature PRs via copilot (not-started)