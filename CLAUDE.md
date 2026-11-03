# Claude — Quant Intelligence Development Instructions

You are contributing to Quant Intelligence, an established Python quantitative finance platform.

## Required project context

Before proposing or implementing substantial changes, read:

1. `PROJECT_HANDOFF.md`
2. `AGENTS.md`
3. The relevant source files and existing tests.

The repository code and tests take priority over historical documentation when they disagree.

## Development rules

- Preserve existing functionality.
- Never work directly on `main`.
- Use a descriptive feature branch.
- Keep changes focused on the assigned task.
- Reuse existing pricing, Greeks, risk, and numerical modules.
- Do not duplicate established functionality.
- Maintain the existing premium navy, white, and pink visual design.
- Add or update tests for behavioral changes.
- Run relevant tests and linting before proposing a merge.
- Never expose API keys, credentials, or secrets.
- Never deploy, force-push, delete branches, or merge Pull Requests without explicit authorization.

## Collaboration

Another developer and AI coding assistant may work on the repository simultaneously.

Do not overwrite unrelated changes.

Use GitHub Pull Requests to propose completed work.

Each Pull Request must explain the changes, tests performed, and potential risks.

## Before beginning a task

Check the current Git branch and working tree.

Inspect the relevant existing implementation.

Briefly explain the intended change and any risks.

Prefer small, reviewable changes.

## Definition of done

A task is complete only when it is correctly implemented, validated, appropriately tested, documented where necessary, and ready for human review.

When uncertain, investigate the actual code rather than guessing.
