"""Compatibility entry point for the Discover browser regression in CI."""
import runpy
import sys
from pathlib import Path

sys.argv += ["--base", "http://127.0.0.1:18514"]
runpy.run_path(str(Path(__file__).with_name("discover_polish_browser.py")), run_name="__main__")
