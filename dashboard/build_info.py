"""Nonsecret source/runtime provenance. Source identity is not host attestation."""

import os
import platform
import re
import subprocess
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path


@lru_cache(maxsize=1)
def build_info():
    sha = os.environ.get("QI_BUILD_SHA", "")
    origin = "injected build identifier"
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        try:
            sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                timeout=2,
            ).strip()
            origin = "checkout source; not an immutable deployment attestation"
        except (OSError, subprocess.SubprocessError):
            sha, origin = "unavailable", "host build identity unverified"
    return {
        "source_sha": sha,
        "identity_basis": origin,
        "python": platform.python_version(),
        **{
            name: version(name)
            for name in ("streamlit", "numpy", "pandas", "scipy", "fastapi")
        },
    }
