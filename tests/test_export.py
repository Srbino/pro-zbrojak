"""Test markdown exportu pro Claude Code."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_question() -> dict:
    return {
        "id": "abc123",
        "pdf_number": 711,
        "section": "nauka_o_zbranich",
        "question": "Vyberte správnou odpověď:",
        "image": "images/abc123.png",
        "options": {
            "A": "Závěr je označen číslem 3.",
            "B": "Tělo zbraně je označeno 1 a 4.",
            "C": "Závěr je označen čísly 3 a 2.",
        },
        "correct": "C",
        "source_page": 188,
        "source_pdf": "test.pdf",
        "parsed_at": "2026-04-15T10:00:00Z",
    }


def test_export_single_creates_file(sample_question, tmp_path, monkeypatch):
    import src.export.claude_md as claude_md
    monkeypatch.setattr(claude_md, "EXPORT_DIR", tmp_path)
    path = claude_md.export_single(sample_question, my_answer="A", note="nevěděl jsem")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Q 711" not in text  # heading uses different format
    assert "č. 711" in text
    assert "C — Závěr je označen čísly 3 a 2." in text
    assert "Moje odpověď:** A (❌ špatně)" in text
    assert "nevěděl jsem" in text
    assert "zákona č. 90/2024" in text  # prompt template


def test_export_questions_bulk(sample_question, tmp_path, monkeypatch):
    import src.export.claude_md as claude_md
    monkeypatch.setattr(claude_md, "EXPORT_DIR", tmp_path)
    q2 = dict(sample_question, id="def456", pdf_number=712, image=None,
              question="Druhá otázka", options={"A": "Aaaa", "B": "Bbbb", "C": "Cccc"}, correct="A")
    path = claude_md.export_questions([sample_question, q2], filename_hint="bulk")
    text = path.read_text(encoding="utf-8")
    assert "č. 711" in text and "č. 712" in text
    assert text.count("---") >= 2
    assert "počet otázek: 2" in text


def test_export_omits_my_answer_when_unspecified(sample_question, tmp_path, monkeypatch):
    import src.export.claude_md as claude_md
    monkeypatch.setattr(claude_md, "EXPORT_DIR", tmp_path)
    path = claude_md.export_single(sample_question)
    text = path.read_text(encoding="utf-8")
    assert "Moje odpověď" not in text
