"""History-aware selected high-confidence patterns. Reports IDs, never secrets.

This is a bounded pattern scan, not entropy scanning or proof of no credentials.
"""

import subprocess

patterns = [
    rb"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"gh[pousr]_[A-Za-z0-9]{30,}",
    rb"AKIA[A-Z0-9]{16}",
    rb"sk-proj-[A-Za-z0-9_-]{40,}",
]
revisions = subprocess.check_output(
    ["git", "rev-list", "--all"], text=True
).splitlines()
failures = []
for revision in revisions:
    result = subprocess.run(
        [
            "git",
            "grep",
            "-I",
            "-l",
            "-E",
            "-e",
            "|".join(x.decode() for x in patterns),
            revision,
            "--",
            ":!scripts/scan_secret_history.py",
        ],
        capture_output=True,
    )
    if result.returncode == 0:
        failures.append(revision)
    elif result.returncode != 1:
        raise RuntimeError("History scan failed")
if failures:
    raise SystemExit(
        f"Potential credentials in {len(failures)} commits; inspect privately and rotate as needed"
    )
print(
    f"No selected high-confidence secret patterns found in {len(revisions)} reachable commits"
)
