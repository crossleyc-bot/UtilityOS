# CLAUDE.md — UtilityOS

## Project Overview

UtilityOS is a new project in early-stage development. The repository currently contains only the initial scaffolding. This file serves as the authoritative reference for AI assistants working in this codebase.

## Repository Structure

```
UtilityOS/
├── CLAUDE.md        # AI assistant guide (this file)
└── README.md        # Project readme
```

The project has no source code, build system, or tooling configured yet. This section should be updated as directories and files are added.

## Development Setup

No build tools, package managers, or runtime dependencies are configured yet. Update this section when a technology stack is chosen.

## Build & Run

No build or run commands exist yet. Update this section as build tooling is introduced.

## Testing

No test framework is configured yet. Update this section when tests are added.

## Code Style & Conventions

Until project-specific linters or formatters are configured, follow these baseline conventions:

- Use clear, descriptive names for files, functions, and variables
- Keep functions short and focused on a single responsibility
- Prefer readability over cleverness
- Add comments only where the intent isn't obvious from the code itself

## Git Workflow

- **Default branch**: `master`
- **Feature branches**: Use descriptive branch names (e.g., `feature/add-auth`, `fix/login-bug`)
- **Commit messages**: Write in imperative mood, keep the subject line under 72 characters, and explain *why* a change was made when it isn't obvious

## Guidelines for AI Assistants

- **Read before modifying** — Always read a file before editing it
- **Prefer edits over new files** — Modify existing files rather than creating new ones unless a new file is clearly needed
- **Keep it simple** — Don't over-engineer or add speculative features
- **Update this file** — When you add new tooling, directories, scripts, or conventions, update the relevant sections of this CLAUDE.md to keep it current
- **No secrets** — Never commit `.env` files, API keys, or credentials
