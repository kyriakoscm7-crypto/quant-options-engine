"""Emit nonsecret review provenance; never claims a deployment occurred."""

import hashlib
import json
import os
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sha = (
    os.environ.get("QI_BUILD_SHA")
    or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
)
print(
    json.dumps(
        {
            "schema_version": 1,
            "source_sha": sha,
            "production_base": "3611d515b22b87a323785320bfafa8ed41748a31",
            "dependency_lock_sha256": hashlib.sha256(
                (root / "requirements.lock").read_bytes()
            ).hexdigest(),
            "python": platform.python_version(),
            "packages": {
                name: version(name)
                for name in ("streamlit", "numpy", "pandas", "scipy", "fastapi")
            },
            "deployment_status": "review artifact; host deployment not attested",
        },
        indent=2,
    )
)
