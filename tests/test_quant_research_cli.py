"""Tests for the automated research command."""

import json
import sys

import pandas as pd
import pytest

from app.forecasting.research_runner import ResearchRunResult
from scripts import run_quant_research


def test_research_command_creates_reports(monkeypatch, tmp_path):
    calls = []

    def fake_run_research(**kwargs):
        calls.append(kwargs)

        return ResearchRunResult(
            predictions=pd.DataFrame(),
            scores=pd.DataFrame(
                [
                    {
                        "Stock": "AAPL",
                        "Sector": "Technology",
                        "Horizon": 5,
                        "Model": "ML",
                        "N": 100,
                        "Brier": 0.24,
                        "Log Loss": 0.68,
                    }
                ]
            ),
            data_quality=pd.DataFrame(
                [
                    {
                        "Stock": "AAPL",
                        "Status": "Valid",
                        "Observations": 3000,
                    }
                ]
            ),
        )

    monkeypatch.setattr(
        run_quant_research,
        "run_research",
        fake_run_research,
    )

    output = tmp_path / "research"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_quant_research",
            "--stocks",
            "AAPL",
            "--years",
            "10",
            "--step",
            "5",
            "--output",
            str(output),
        ],
    )

    run_quant_research.main()

    assert len(calls) == 1
    assert calls[0]["years"] == 10
    assert calls[0]["step"] == 5
    assert len(calls[0]["stocks"]) == 1
    assert calls[0]["stocks"][0].ticker == "AAPL"

    assert (output / "validation_scores.csv").exists()
    assert (output / "data_quality.csv").exists()
    assert (output / "experiment_metadata.json").exists()

    metadata = json.loads(
        (output / "experiment_metadata.json").read_text()
    )

    assert metadata["research_period"] == "Validation"
    assert metadata["reserved_test_evaluated"] is False
    assert metadata["stocks"] == ["AAPL"]

    scores = pd.read_csv(output / "validation_scores.csv")
    assert scores.iloc[0]["Brier"] == pytest.approx(0.24)


@pytest.mark.parametrize(
    "arguments",
    [
        ["--years", "0"],
        ["--step", "0"],
        ["--stocks", "AAPL", "AAPL"],
    ],
)
def test_invalid_arguments_are_rejected(monkeypatch, arguments):
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_quant_research", *arguments],
    )

    with pytest.raises(SystemExit) as error:
        run_quant_research.main()

    assert error.value.code == 2


def test_ticker_normalization(monkeypatch, tmp_path):
    captured = []

    def fake_run_research(**kwargs):
        captured.extend(kwargs["stocks"])

        return ResearchRunResult(
            predictions=pd.DataFrame(),
            scores=pd.DataFrame(),
            data_quality=pd.DataFrame(
                [{"Stock": "AAPL", "Status": "Valid"}]
            ),
        )

    monkeypatch.setattr(
        run_quant_research,
        "run_research",
        fake_run_research,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_quant_research",
            "--stocks",
            "aapl",
            "--output",
            str(tmp_path),
        ],
    )

    run_quant_research.main()

    assert captured[0].ticker == "AAPL"
    assert captured[0].sector == "Technology"
