"""Unit-тесты лимитов judge без Docker."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_JUDGE_PATH = Path(__file__).resolve().parent / "judge.py"


def _load_judge():
    spec = importlib.util.spec_from_file_location(
        "sandbox_judge", _JUDGE_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_output_too_large_detects_oversize() -> None:
    judge = _load_judge()
    big = "x" * (judge._MAX_OUTPUT_BYTES + 10)
    assert judge._output_too_large(big, "") is True
    assert judge._output_too_large("ok", "") is False


def test_work_tree_violation_too_many_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    judge = _load_judge()
    monkeypatch.setattr(judge, "WORK_DIR", tmp_path)
    monkeypatch.setattr(judge, "_MAX_WORK_FILES", 3)
    for i in range(4):
        (tmp_path / f"f{i}.txt").write_text("a")
    msg = judge._work_tree_violation()
    assert msg is not None
    assert "Слишком много файлов" in msg


def test_work_tree_violation_large_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    judge = _load_judge()
    monkeypatch.setattr(judge, "WORK_DIR", tmp_path)
    monkeypatch.setattr(judge, "_MAX_WORK_FILE_BYTES", 8)
    (tmp_path / "big.bin").write_bytes(b"0123456789")
    msg = judge._work_tree_violation()
    assert msg is not None
    assert "слишком большой" in msg.lower()
