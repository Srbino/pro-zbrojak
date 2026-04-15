"""Pydantic models for parsed questions."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


Section = Literal["pravo", "provadeci_predpisy", "jine_predpisy", "nauka_o_zbranich", "zdravotni_minimum"]


class Options(BaseModel):
    A: str
    B: str
    C: str


class Question(BaseModel):
    id: str  # SHA-1 hash of question text
    pdf_number: int
    section: Section | None = None
    question: str
    image: str | None = None  # relative path under repo root
    options: Options
    correct: Literal["A", "B", "C"]
    source_page: int
    source_pdf: str
    parsed_at: str  # ISO timestamp


class UnparsedQuestion(BaseModel):
    pdf_number: int
    source_page: int
    raw_text: str
    reason: str
