<!--
  Sync Impact Report
  ==================
  Version change: (template) → 1.0.0
  Modified principles: N/A (all new — first adoption)
  Added sections:
    - Core Principles (5 principles)
      - I. Desktop Linux First
      - II. Clean Architecture
      - III. Test-First (NON-NEGOTIABLE)
      - IV. Internationalization First
      - V. Open-Source Governance
    - Technology Stack & Toolchain
    - Development Workflow
    - Governance (with amendment procedure, versioning policy, compliance review)
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md     ⚠ pending (Constitution Check gates need filling per plan)
    - .specify/templates/spec-template.md     ✅ no changes required
    - .specify/templates/tasks-template.md    ✅ no changes required
  Commands checked:
    - .specify/templates/commands/            N/A — directory does not exist
  Follow-up TODOs: none — all placeholders resolved
-->

# myTime — Gerenciador Inteligente de Tempo — Constitution

## Core Principles

### I. Desktop Linux First
All development MUST target Linux desktop as the primary platform.
The application MUST integrate with system tray, desktop notifications
(`notify-send`), and follow FreeDesktop standards (`.desktop` entries,
icons, MIME types). Cross-platform compatibility is a secondary concern
and MUST NOT compromise Linux-native quality or user experience.

**Rationale**: myTime is built for the Linux desktop ecosystem. Deep
integration with system tray, notifications, and window management is
core to the Pomodoro/work-journey experience.

### II. Clean Architecture
Code MUST follow a strict separation of concerns across three layers:
- `core/` — business logic (engine, models, storage) with zero imports
  from `ui/` modules
- `ui/` — presentation layer (Qt windows, tray, dialogs)
- `utils/` — cross-cutting utilities (icons, audio, notifications)

Core modules MUST be independently testable without a running Qt event
loop. Data persistence MUST be abstracted behind storage interfaces.

**Rationale**: Separating core logic from UI enables reliable unit
testing, simplifies maintenance, and allows future GUI replacements.

### III. Test-First (NON-NEGOTIABLE)
Test-Driven Development is mandatory. The Red-Green-Refactor cycle MUST
be strictly followed:
1. Write a failing test first
2. Confirm the test fails
3. Implement the minimum code to pass
4. Refactor while keeping tests green

All tests MUST pass before merging. `core/` modules require minimum 80%
line coverage. UI tests (pytest-qt) MUST cover all user-facing dialogs
and tray interactions.

**Rationale**: Pomodoro timing correctness is critical — off-by-one
errors or race conditions directly impact user trust. Test-first
discipline prevents regressions in timing-sensitive code.

### IV. Internationalization First
All user-facing strings MUST be externalized to locale JSON files under
`locales/`. Every feature MUST ship with both `pt_BR` and `en_US`
translations before being considered complete. String freeze MUST
precede any feature release.

New languages MAY be added by contributing a new locale file. No
hardcoded UI strings are permitted.

**Rationale**: The project serves both Portuguese and English audiences
from day one. Retrofitting i18n is significantly more expensive than
building it in from the start.

### V. Open-Source Governance
The project is distributed under the MIT license. All contributions
MUST follow the standard fork-branch-PR workflow. Every dependency
MUST be open-source and license-compatible with MIT.

External contributions MUST:
- Follow the same Test-First principle
- Include locale entries for all supported languages
- Pass all lint (ruff), type (mypy), and test gates

**Rationale**: MIT license maximizes adoption and contribution. Clear
governance ensures long-term project health and contributor clarity.

## Technology Stack & Toolchain

- **Language**: Python 3.11+
- **GUI Framework**: PySide6 (Qt6)
- **Testing**: pytest, pytest-qt, pytest-cov
- **Linting**: ruff (line-length 100, select E/F/I/UP/W)
- **Type Checking**: mypy (warn-return-any, disallow-untyped-defs preferred)
- **Build/Package**: setuptools, PyInstaller, Flatpak, AppImage
- **Notifications**: notify-send / libcanberra / PulseAudio / ALSA
- **All tooling configuration** MUST live in `pyproject.toml`

## Development Workflow

1. **Branching**: Feature branches from `main` using conventional names
   (`feat/`, `fix/`, `chore/`)
2. **Commits**: Conventional Commits format
   (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
3. **PR Gates** (all MUST pass before merge):
   - ✅ All tests pass (`pytest`)
   - ✅ Lint passes (`ruff check`)
   - ✅ Type check passes (`mypy`)
   - ✅ Coverage meets thresholds
4. **Code Review**: Every PR requires at least one approval
5. **No direct pushes** to `main` — only merge commits from PRs

## Governance

**Supremacy**: This Constitution supersedes all ad-hoc development
practices. All code, reviews, and planning MUST comply with these
principles.

**Amendment Procedure**:
1. A documented proposal describing the change and its rationale
2. Consensus from active maintainers
3. Version bump per semver rules
4. Updated constitution committed to repository

**Versioning Policy**:
- MAJOR: Backward-incompatible principle removal or redefinition
- MINOR: New principle or materially expanded guidance
- PATCH: Clarifications, typo fixes, non-semantic refinements

**Compliance Review**: Annual review of all active features against
constitution principles. Non-compliant code MUST be documented with
a remediation plan.

**Version**: 1.0.0 | **Ratified**: 2026-07-02 | **Last Amended**: 2026-07-02
