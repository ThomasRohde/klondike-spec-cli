# VS Code GitHub Copilot Customization Playbook (for Codex)

**Audience:** An LLM coding agent called **Codex** that can edit this repository and is aware of GitHub Copilot + VS Code.

**Goal:**  
Given a natural-language request like _“Create a prompt to update the project version”_, Codex should:

1. Decide whether this is:
   - A **repo-wide rule change** (custom instructions),
   - A **reusable task** (prompt file),
   - Or a **specialist role** (custom agent).
2. Create or update the relevant Markdown + VS Code settings:
   - `.github/copilot-instructions.md`
   - `.github/instructions/*.instructions.md`
   - `.github/prompts/*.prompt.md`
   - `.github/agents/*.agent.md`
   - `.vscode/settings.json`
3. Keep everything **idempotent**, **diff-friendly**, and **safe**.

---

## 1. Assumptions & constraints

You, Codex:

- Can read/write files in this repo.
- **Must not**:
  - Enable global YOLO (`chat.tools.global.autoApprove: true`) unless explicitly asked.
  - Add instructions that encourage destructive shell commands or unsafe automation.
- Prefer:
  - Small, composable files.
  - Clear sections and lists over walls of text.
  - Changes that are easy to review in a diff.

---

## 2. Copilot customization primitives

### 2.1 Repo-wide instructions

**Files**

- Global repo instructions:  
  - `.github/copilot-instructions.md`
- Path-specific instructions:
  - `.github/instructions/<topic>.instructions.md`

**Semantics**

- `copilot-instructions.md`: broad rules that always apply in this repo (coding style, testing expectations, security posture, etc.).
- `*.instructions.md`: more focused rules for specific paths / languages, selected via `applyTo` glob patterns.

**Recommended structure: `.github/copilot-instructions.md`**

When you create or edit this file, keep it structured:

```markdown
# Copilot Instructions for This Repository

## Project Overview
- Short 3–5 bullet description of the project and its purpose.

## Coding Standards
- Language choices and versions (e.g., "Use TypeScript over JS", "Use Python 3.12+").
- Style / linting rules at a high level.
- Error handling and logging principles.

## Testing & Quality
- Required test frameworks.
- Minimal expectations for coverage and regression tests.
- When to add / update tests.

## Security & Compliance
- Any security rules Copilot should always respect.
- Data handling / PII rules.
- Forbidden libraries or patterns, if any.

## Tooling & Workflows
- Any specific workflows (e.g., migrations, release process) that Copilot should be aware of.
```

You may append / update sections instead of rewriting the whole file.

---

### 2.2 Path-specific instructions

**Files**

- Located under: `.github/instructions/`
- Name pattern: `NAME.instructions.md`
- Must start with a YAML frontmatter block that includes `applyTo`.

**Example template:**

```markdown
---
description: "Python files: testing and style rules"
applyTo: "**/*.py"
---

# Python Instructions

- Prefer type-annotated functions.
- Use pytest for testing.
- Avoid side effects at import time.
```

Rules:

1. **Never remove** existing `applyTo` unless user explicitly wants to retarget it.
2. Keep each `*.instructions.md` file focused on a topic (e.g., `python`, `tests`, `security`, `frontend`).
3. If the user request is clearly scoped to a stack / path (e.g. “React frontend tests”), add or adjust a specific `*.instructions.md` instead of stuffing everything into `copilot-instructions.md`.

---

### 2.3 Prompt files (reusable tasks)

**Files**

- Workspace prompt files: `.github/prompts/<slug>.prompt.md`
- Each file defines a reusable prompt that appears as a slash command (`/<name>`) in Copilot Chat.

**Core structure**

```markdown
---
name: update-version
description: "Update project version across configuration and manifest files."
argument-hint: "<new_version> (e.g. 1.4.0)"
agent: agent
model: GPT-4o
tools:
  - githubRepo
  - search/codebase
---

# Goal

You help maintainers update the project version consistently.

## Context

- The user will specify the desired new version in chat (for example: `1.4.0`).
- The repository may contain multiple manifests (examples: `package.json`, `package-lock.json`, `pyproject.toml`, `setup.cfg`, `.csproj`, Dockerfiles, Helm charts, etc.).

## Instructions

1. **Clarify the target version**
   - If the user’s version is ambiguous or missing, ask a brief clarification question.
   - Confirm the final version string you will apply.

2. **Scan the codebase**
   - Use the available tools to identify files where a version is defined.
   - Prioritize:
     - Language/package manifests (npm, PyPI, NuGet, Maven, etc.).
     - CI/CD or deployment manifests that reference the project version.
     - Documentation where version appears in a clearly “current version” context.

3. **Plan the changes**
   - Propose a short plan listing:
     - Which files will be updated.
     - Which existing version(s) will be replaced.
   - Wait for user confirmation if the plan looks risky or touches many files.

4. **Apply the changes**
   - Update all relevant version fields to the new value in a consistent way.
   - Avoid changing:
     - Historical changelog entries.
     - Archived release notes.
     - Example code that deliberately shows older versions.

5. **Validate**
   - Where appropriate, suggest or run relevant commands (e.g. tests, linters, build) according to repo instructions.
   - If commands fail, summarize the failure and propose a fix; do not hide errors.

6. **Summarize**
   - List all files changed.
   - Show a high-level diff summary (sections / fields touched).
   - Mention any follow-up manual steps for the maintainer (e.g., “tag release”, “update documentation URL”).

## Output Formatting

- Start with a **bullet list of actions taken**.
- Include a short **table of changed files** and their role (manifest, CI, docs).
- Provide any suggested commands in a fenced code block.
```

You will adapt this pattern to other tasks.

---

### 2.4 Custom agents

**Files**

- Location: `.github/agents/<slug>.agent.md`
- Purpose: define specialized agents (e.g., `@release-engineer`, `@security-review`, `@docs-writer`).

**Minimal template:**

```markdown
---
name: release-engineer
description: "Specialist agent for planning and executing releases (versioning, changelog, tagging, release notes)."
model: GPT-4o
tools:
  - githubRepo
  - search/codebase
  - terminal
---

# Role

You act as a release engineer for this repository.

## Responsibilities

- Interpret release requirements (semantic versioning, release scope).
- Coordinate with instructions from `.github/copilot-instructions.md`.
- Use reusable prompt files (for example `/update-version`) instead of re-inventing logic.
- Propose safe, reviewable plans and avoid destructive operations.

## Behavior

- Always explain your plan before making changes.
- Prefer editing files and opening changes for review instead of directly running destructive commands.
- Treat instructions files and prompt files as authoritative for coding style, tests, and security.
```

Only create or edit a custom agent when the user explicitly wants a **role** (e.g. “give me a release engineer agent profile”).

---

## 3. VS Code configuration you are allowed to touch

**File**

- `.vscode/settings.json` (workspace-level)

### 3.1 Ensure Copilot sees instructions & prompts

When needed, create or update `.vscode/settings.json` to include (merge, don’t overwrite):

```jsonc
{
  // Use repo instructions files
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,

  // Where to look for instructions
  "chat.instructionsFilesLocations": {
    ".github/instructions": true
  },

  // Enable prompt files and their location
  "chat.promptFiles": true,
  "chat.promptFilesLocations": {
    ".github/prompts": true
  },

  // Optional: chat modes if we add them later
  "chat.modeFilesLocations": {
    ".github/chatmodes": true
  }
}
```

Merge behavior:

1. If `settings.json` does not exist, create it with a minimal object containing the above.
2. If it exists:
   - Parse as JSON.
   - Only add / update the keys listed above.
   - Preserve unrelated settings.

### 3.2 Safety defaults for tools

You may **enforce** safe defaults if they are missing (but do not enable YOLO):

```jsonc
{
  "chat.tools.terminal.autoApprove": {
    "rm": false,
    "rmdir": false,
    "del": false,
    "kill": false,
    "chmod": false,
    "chown": false,
    "/^Remove-Item\b/i": false
  },
  "chat.tools.global.autoApprove": false
}
```

- Never set `"chat.tools.global.autoApprove": true` unless the user explicitly asks you to and acknowledges the risk.
- If you detect it is already `true`, you may warn the user in your explanation, but **do not silently flip it**.

---

## 4. How to respond to user requests (Codex behavior)

When the user gives you a prompt like:

> “Create a prompt to update the project version”

follow this decision tree.

### 4.1 Classify the request

1. **Repo-wide policy change?**  
   Examples:
   - “Copilot should always use pytest.”
   - “For this repo, commit messages must follow Conventional Commits.”

   → Update `.github/copilot-instructions.md` (and possibly add a focused `*.instructions.md`).

2. **Reusable task / workflow?**  
   Examples:
   - “Create a prompt to update the project version.”
   - “Create a prompt to generate feature flags.”
   - “Create a prompt to scaffold a new React page.”

   → Create or update a prompt file in `.github/prompts/*.prompt.md`.

3. **Specialist role?**  
   Examples:
   - “Create a deployment SRE agent.”
   - “Create a data-migration agent.”

   → Create or update `.github/agents/<slug>.agent.md`.

If unclear, default to a **prompt file**; it’s the least intrusive and most reusable.

---

### 4.2 Algorithm for creating / updating a prompt file

Given a task description like:

> “Create a prompt to update the project version.”

do the following:

1. **Derive identifiers**
   - `slug`: kebab-case version of the task, e.g. `update-project-version`.
   - `file`: `.github/prompts/update-project-version.prompt.md`.
   - `name` (frontmatter): short slash command name, e.g. `update-version`.

2. **If the prompt file exists**
   - Parse existing YAML frontmatter and body.
   - Preserve:
     - `name`, if stable;
     - any explicit `tools`, `model`, `agent`, unless user requested changes.
   - Update:
     - `description` to clearly reflect the task.
     - Body instructions to follow the pattern in section **2.3**.

3. **If the prompt file does not exist**
   - Create it with:
     - A frontmatter block including `name`, `description`, `argument-hint`, `agent`, `model`, `tools`.
     - A body containing:
       - **Goal** section
       - **Context** section
       - **Instructions** section as explicit steps
       - **Output formatting** section

4. **Tie into other config**
   - Ensure `.vscode/settings.json` includes `chat.promptFiles: true` and `chat.promptFilesLocations` pointing at `.github/prompts`.
   - If relevant instructions already live in `.github/copilot-instructions.md` or `*.instructions.md`, reference them in the prompt body instead of duplicating text (for example: “Follow the testing rules defined in `.github/instructions/tests.instructions.md` when deciding which tests to update or run.”).

5. **Explain the change**
   - In your chat output, summarize:
     - The prompt file name.
     - The slash command name (`/update-version`).
     - How the user should trigger it and what arguments they should pass.

---

### 4.3 Algorithm for updating repo-wide instructions

Given a request like:

> “Make sure Copilot always uses semantic versioning and documents it in release notes.”

1. Create or update `.github/copilot-instructions.md`.
2. Append or modify the relevant sections:
   - Under “Coding Standards” or “Tooling & Workflows”, add bullets describing:
     - Semantic versioning rules (major/minor/patch).
     - Expectations for release notes.
3. If this also affects only some paths (e.g. just a `backend/` folder), create a more specific `backend.instructions.md` with `applyTo: "backend/**"`.

When editing instructions:

- Keep bullets short and imperative.
- Don’t duplicate rules that already exist in other sections or instruction files; instead reference them.

---

### 4.4 Algorithm for creating a custom agent

Given a request like:

> “Create a release engineer agent based on our instructions and versioning prompt.”

1. Derive:

   - `slug`: `release-engineer`
   - `file`: `.github/agents/release-engineer.agent.md`
   - `name`: `release-engineer` or a nicer display name like `"Release Engineer"`

2. If the file exists:
   - Merge new responsibilities into the prompt body.
   - Do **not** remove existing `tools` unless asked.

3. If the file is new:
   - Create using the template in **2.4**, but:
     - Reference relevant instructions and prompt files explicitly in the body (e.g. “Use the `/update-version` prompt for version changes.”).

4. Ensure `.vscode/settings.json` includes:

```jsonc
{
  "chat.modeFilesLocations": {
    ".github/chatmodes": true
  },
  "chat.useAgentsMdFile": true
}
```

(Only if chat modes / AGENTS.md usage is part of the intended workflow. If not, you may omit this.)

---

## 5. Concrete example: “Update project version” prompt file

When the user says:

> “Create a prompt to update the project version.”

you should **at minimum** create this file:

` .github/prompts/update-project-version.prompt.md`

with content similar to:

```markdown
---
name: update-version
description: "Update the project version across manifests and related configuration."
argument-hint: "<new_version> (for example: 1.4.0)"
agent: agent
model: GPT-4o
tools:
  - githubRepo
  - search/codebase
---

# Goal

Help the maintainer safely and consistently update the project version across all relevant files in this repository.

## Context

- The user will provide the desired new version (for example, `1.4.0`) in chat when triggering this prompt.
- The repository may contain multiple files that define or mirror the project version:
  - Package manifests (e.g. `package.json`, `pyproject.toml`, `.csproj`, `pom.xml`, `Cargo.toml`).
  - Lock files (e.g. `package-lock.json`, `yarn.lock`) where appropriate.
  - CI/CD pipelines and deployment manifests.
  - Documentation sections that explicitly indicate the current version.

## Instructions

1. **Clarify the version**
   - If the user didn’t specify a version or gave an ambiguous one, ask a short clarifying question.
   - Once clear, repeat the version you will apply.

2. **Discover existing versions**
   - Use the available tools to locate version declarations and references.
   - Prioritize:
     - Primary project version fields (package / project metadata).
     - Release / deployment manifests that must stay in sync.
   - Ignore:
     - Historical changelogs.
     - Archived documentation or examples that intentionally show older versions.

3. **Propose a plan**
   - List all files and locations you intend to change.
   - For each file, show the **current version** and the **new version**.
   - Wait for user confirmation if the scope is surprising or large.

4. **Apply changes**
   - Update all agreed version fields to the new version string.
   - Maintain existing formatting (indentation, quoting style, etc.).
   - If multiple versions are present (monorepo, multiple packages), either:
     - Ask which subset to update, or
     - Clearly separate changes per package.

5. **Validate**
   - If the repo instructions define tests or checks, follow them.
   - Suggest relevant commands (tests, builds, linters). Run them only when appropriate and allowed.
   - If any command fails, summarize the failure and suggest concrete fixes.

6. **Summarize the result**
   - Provide a bullet list of all changed files and version fields.
   - Include short diff-style snippets for the most important changes.
   - Call out any follow-up manual steps (e.g. tagging a release, updating release notes).

## Output Format

- Start with: `Summary` section (bullet list).
- Then `Changed files` section with a small table:

  | File | Role | From | To |
  |------|------|------|----|

- End with `Suggested commands` section containing any useful commands in a shell code block.
```

You may refine this template if the repository has a clearly defined release process documented in `.github/copilot-instructions.md` or `*.instructions.md`, but keep the structure recognizable.

---

## 6. What you must always do

- Keep all modifications **reviewable and reversible**.
- Integrate with existing instructions and prompts instead of duplicating logic.
- When in doubt, prefer:
  - One new prompt file over complex inline chat instructions.
  - One new `*.instructions.md` (with a clear `applyTo`) over adding unrelated rules to `copilot-instructions.md`.
- Always explain to the user **what you created or changed** and **how to trigger it** in VS Code Copilot Chat.
