"""Explicit isolated local API mode; each test gets a fresh request budget."""
import os
import sys

import pytest

os.environ["QI_API_MODE"] = "development"

@pytest.fixture(autouse=True)
def fresh_api_budget():
    module = sys.modules.get("app.api.main")
    layer = module.app.middleware_stack if module else None
    while layer is not None:
        if hasattr(layer, "request_times"):
            layer.request_times.clear()
        layer = getattr(layer, "app", None)


@pytest.fixture(autouse=True)
def isolated_sec_budget(tmp_path, monkeypatch):
    """Offline provider tests must not share operator cooldown state."""
    from app.intelligence import sec_access

    monkeypatch.setattr(sec_access, "BUDGET_PATH", str(tmp_path / "sec-budget.json"))
