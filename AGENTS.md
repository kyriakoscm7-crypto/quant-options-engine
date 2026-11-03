# Quant Intelligence — Shared AI Development Rules

## Project identity

Quant Intelligence is an established Python-based financial research application using Streamlit, FastAPI, and quantitative analysis modules.

Read `PROJECT_HANDOFF.md` for background, architecture, historical decisions, and product direction.

## Source of truth

Use this priority:

1. Current repository code and configuration.
2. Verified tests and runtime behavior.
3. Git history and Pull Requests.
4. Current maintained documentation.
5. Historical project handoff.

Never assume historical feature descriptions exactly match the current codebase.

## Safety

- Do not modify `main` directly.
- Do not force-push.
- Do not delete unrelated files.
- Do not reset or overwrite uncommitted changes.
- Do not access or expose production secrets unnecessarily.
- Do not deploy without explicit authorization.
- Never bypass failing checks merely to complete a task.

## Engineering

- Preserve existing working behavior.
- Maintain mathematical correctness.
- Reuse shared quantitative functions.
- Follow established naming, formatting, and architecture.
- Keep changes small and focused.
- Add regression tests for bugs.
- Update relevant tests for new functionality.
- Verify dependency compatibility.

## Product and interface

Maintain the established premium visual identity:

- Primary accent: `#FF78B7`
- Deep background: `#080D1D`
- Secondary background: `#0D1424`
- Elevated surfaces: `#121D35`

Prioritize usability, responsiveness, transparent financial assumptions, and integration between features.

Avoid unnecessary page proliferation.

## Pull Requests

Each proposed change should include:

- Summary of changes.
- Motivation.
- Files or components affected.
- Tests executed.
- Screenshots for visual changes where useful.
- Risks and limitations.

## Completion

Report what was changed and what was actually tested.

Distinguish verified outcomes from assumptions.

Do not claim deployment or test success without evidence.
