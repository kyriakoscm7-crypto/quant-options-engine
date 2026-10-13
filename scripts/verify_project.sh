#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

mkdir -p .quality_reports

REPORT=".quality_reports/latest_verification.log"

echo "QUANT INTELLIGENCE — AUTOMATED QUALITY VERIFICATION"
echo "==================================================="

{
    echo "Timestamp: $(date)"
    echo "Branch: $(git branch --show-current)"
    echo "Commit: $(git rev-parse --short HEAD)"
    echo

    echo "===== CODE QUALITY ====="
    python -m ruff check app dashboard tests

    echo
    echo "===== AUTOMATED TESTS ====="
    python -m pytest tests -q

    echo
    echo "===== GIT WHITESPACE CHECK ====="
    git diff --check

    echo
    echo "===== GIT STATUS ====="
    git status --short

    echo
    echo "VERIFICATION PASSED"
} 2>&1 | tee "$REPORT"
