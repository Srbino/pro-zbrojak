"""Loader pro questions.json + indexy."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
QUESTIONS_PATH = ROOT / "data" / "questions.json"


@lru_cache(maxsize=1)
def load_questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def by_id() -> dict[str, dict]:
    return {q["id"]: q for q in load_questions()}


def by_pdf_number() -> dict[int, dict]:
    return {q["pdf_number"]: q for q in load_questions()}


def by_section(section: str) -> list[dict]:
    return [q for q in load_questions() if q.get("section") == section]
