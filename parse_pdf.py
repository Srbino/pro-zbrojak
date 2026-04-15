#!/usr/bin/env python3
"""
Parser oficiálního PDF MV ČR „Soubor testových otázek pro teoretickou část ZOZ".

Výstup:
  data/questions.json  — pole otázek (Pydantic Question)
  data/unparsed.json   — otázky, kde se nepodařilo detekovat správnou odpověď
  images/<hash>.png    — obrázky vázané k otázkám

Detekce správné odpovědi: šedé podbarvení (fill ~0.827 grayscale) v PDF rects.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
import pymupdf  # PyMuPDF
from PIL import Image
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.parser.models import Question, Options, UnparsedQuestion, Section


ROOT = Path(__file__).parent
PDF_PATH = ROOT / "MV-Soubor_testovych_otazek_pro_teoretickou_cast_ZOZ_a_komisionalni_zkousku_-_20251215.pdf"
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "images"
LOGS_DIR = ROOT / "logs"

# --- Section ranges from PDF table of contents (str. 1) ---
# Strany jsou 1-based dle obsahu PDF.
SECTION_PAGE_RANGES: list[tuple[int, int, Section]] = [
    (2, 131, "pravo"),
    (132, 147, "provadeci_predpisy"),
    (148, 157, "jine_predpisy"),
    (158, 209, "nauka_o_zbranich"),
    (210, 999, "zdravotni_minimum"),
]

# Šedé podbarvení správné odpovědi
GRAY_FILL_TARGET = 0.827
GRAY_TOLERANCE = 0.05

# Regex
RE_QUESTION_START = re.compile(r"^(\d{1,4})\.(?:\s+(.*))?$")
RE_OPTION = re.compile(r"^([ABCabc])\)\s+(.*)$")

# Font glyph mapping fixes — PDF má rozbitou CMap pro některé glyphy.
# Empiricky odvozeno z porovnání s kontextem (zákonné termíny: identický, nabytí, povinnosti…).
GLYPH_FIXES = {
    "\u019F": "ti",   # Ɵ  → "ti" (capital position in font)
    "\u01A1": "ti",   # ơ  → "ti" (regular weight)
    "\u014C": "ft",   # Ō  → "ft" (paintball / airsoft / software…)
    "\uFB01": "fi",   # ﬁ ligature
    "\uFB00": "ff",
    "\uFB02": "fl",
    "\uFB03": "ffi",
    "\uFB04": "ffl",
    "\u202F": " ",    # narrow no-break space
    "\u00A0": " ",    # nbsp
    "\uFFFD": "ti",   # pdfplumber substitutes broken glyph with replacement char (= same source)
}


def normalize_text(s: str) -> str:
    """Aplikuj glyph fixes a NFKC normalizaci."""
    if not s:
        return s
    for bad, good in GLYPH_FIXES.items():
        if bad in s:
            s = s.replace(bad, good)
    # NFKC normalizes residual compatibility forms
    return unicodedata.normalize("NFKC", s)

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        RichHandler(console=console, show_time=False, show_path=False, markup=True),
        logging.FileHandler(LOGS_DIR / "parser.log", mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger("parser")


def hash_id(question_text: str, opt_a: str = "", opt_b: str = "", opt_c: str = "") -> str:
    """Stable ID = SHA-1 of question text + answer texts. Survives PDF renumbering."""
    payload = f"{question_text}\x1f{opt_a}\x1f{opt_b}\x1f{opt_c}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def section_for_page(page_num: int) -> Section | None:
    for lo, hi, sec in SECTION_PAGE_RANGES:
        if lo <= page_num <= hi:
            return sec
    return None


def is_gray_fill(rect: dict) -> bool:
    """Šedé podbarvení správné odpovědi (~0.827 grayscale)."""
    fill = rect.get("non_stroking_color")
    if fill is None:
        return False
    # pdfplumber vrací buď float, tuple/list (RGB) nebo (k,) gray
    if isinstance(fill, (int, float)):
        return abs(float(fill) - GRAY_FILL_TARGET) <= GRAY_TOLERANCE
    if isinstance(fill, (list, tuple)) and len(fill) == 1:
        return abs(float(fill[0]) - GRAY_FILL_TARGET) <= GRAY_TOLERANCE
    if isinstance(fill, (list, tuple)) and len(fill) == 3:
        r, g, b = (float(c) for c in fill)
        if abs(r - g) < 0.05 and abs(g - b) < 0.05:
            return abs(r - GRAY_FILL_TARGET) <= GRAY_TOLERANCE
    return False


def y_overlap(rect_top: float, rect_bot: float, line_top: float, line_bot: float) -> float:
    """Pixely vertikálního překryvu mezi rectem a řádkem."""
    return max(0.0, min(rect_bot, line_bot) - max(rect_top, line_top))


# ----------------------------- Per-page parsing -----------------------------

def extract_lines_with_bbox(page) -> list[dict]:
    """Vrátí seznam řádků: {text, top, bottom, x0, x1}."""
    words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
    if not words:
        return []
    # group into lines by 'top' proximity
    lines: list[dict] = []
    cur: list[dict] = []
    cur_top = None
    LINE_TOL = 3.0
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if cur_top is None or abs(w["top"] - cur_top) <= LINE_TOL:
            cur.append(w)
            cur_top = w["top"] if cur_top is None else cur_top
        else:
            lines.append(_finalize_line(cur))
            cur = [w]
            cur_top = w["top"]
    if cur:
        lines.append(_finalize_line(cur))
    return lines


def _finalize_line(words: list[dict]) -> dict:
    words_sorted = sorted(words, key=lambda w: w["x0"])
    raw = " ".join(w["text"] for w in words_sorted)
    return {
        "text": normalize_text(raw),
        "top": min(w["top"] for w in words_sorted),
        "bottom": max(w["bottom"] for w in words_sorted),
        "x0": min(w["x0"] for w in words_sorted),
        "x1": max(w["x1"] for w in words_sorted),
    }


# ----------------------------- Question segmentation -----------------------------

class RawQuestion:
    """Mezistupeň: surová otázka před detekcí správné odpovědi."""

    def __init__(self, pdf_number: int, page_num: int, marker_top: float = 0.0):
        self.pdf_number = pdf_number
        self.page_num = page_num
        self.marker_top = marker_top  # y-coord of "N." marker (start of question on the page)
        self.question_lines: list[dict] = []
        self.options: dict[str, list[dict]] = {"A": [], "B": [], "C": []}
        self.current_option: str | None = None

    def add_line(self, line: dict):
        if self.current_option is None:
            self.question_lines.append(line)
        else:
            self.options[self.current_option].append(line)

    def question_text(self) -> str:
        return " ".join(l["text"] for l in self.question_lines).strip()

    def option_text(self, key: str) -> str:
        return " ".join(l["text"] for l in self.options[key]).strip()

    def option_bbox(self, key: str) -> tuple[float, float] | None:
        ls = self.options[key]
        if not ls:
            return None
        return (min(l["top"] for l in ls), max(l["bottom"] for l in ls))


def parse_pages(pdf) -> list[tuple[RawQuestion, list[dict]]]:
    """Projde celé PDF a vrátí list (RawQuestion, gray_rects_pro_jeji_stranky)."""
    questions: list[tuple[RawQuestion, list[dict]]] = []
    current: RawQuestion | None = None
    current_gray_rects: list[dict] = []

    for page_idx, page in enumerate(pdf.pages, start=1):
        lines = extract_lines_with_bbox(page)
        page_gray_rects = [r for r in page.rects if is_gray_fill(r)]

        # Per page, append gray rects to currently open question
        if current is not None:
            for gr in page_gray_rects:
                current_gray_rects.append({**gr, "_page": page_idx})

        for line in lines:
            text = line["text"].strip()
            # Skip empty / page numbers / section headings
            if not text or text.isdigit() or text in {"Soubor testových otázek pro teoretickou část"}:
                continue

            # Try option first (since "A) ..." would be greedily eaten by question regex otherwise)
            m_opt = RE_OPTION.match(text)
            if m_opt and current is not None and current.question_lines:
                key = m_opt.group(1).upper()
                current.current_option = key
                # Replace the line text with content after the prefix
                line_for_opt = {**line, "text": m_opt.group(2)}
                current.options[key].append(line_for_opt)
                continue

            m_q = RE_QUESTION_START.match(text)
            if m_q:
                # close previous
                if current is not None:
                    questions.append((current, current_gray_rects))
                # start new
                num = int(m_q.group(1))
                current = RawQuestion(num, page_idx, marker_top=line["top"])
                current_gray_rects = [{**r, "_page": page_idx} for r in page_gray_rects]
                rest = m_q.group(2) or ""
                if rest.strip():
                    first_line = {**line, "text": rest}
                    current.question_lines.append(first_line)
                continue

            # Continuation line
            if current is not None:
                current.add_line(line)

    if current is not None:
        questions.append((current, current_gray_rects))

    return questions


# ----------------------------- Correct answer detection -----------------------------

def detect_correct(rq: RawQuestion, gray_rects: list[dict]) -> str | None:
    """Vrátí 'A'/'B'/'C' nebo None."""
    scores: dict[str, float] = {"A": 0.0, "B": 0.0, "C": 0.0}
    for key in ("A", "B", "C"):
        bbox = rq.option_bbox(key)
        if bbox is None:
            continue
        opt_top, opt_bot = bbox
        # gray rects on same page-equivalence: we use only y; cross-page is rare for one option
        for r in gray_rects:
            overlap = y_overlap(r["top"], r["bottom"], opt_top, opt_bot)
            scores[key] += overlap
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] < 1.0:  # threshold: must overlap at least 1px
        return None
    return best[0]


# ----------------------------- Image extraction (PyMuPDF) -----------------------------

def extract_images_for_questions(pdf_path: Path, questions: list[tuple[RawQuestion, list[dict]]]):
    """Pro kazdou otazku najde obrazek na jeji strance a RASTERIZUJE ho jako
    vyrez stranky (vcetne overlay, napr. cisel 1-6 nad pistoli).

    Proc rasterizace misto `extract_image(xref)`:
    PDF casto embeduje zakladni JPEG pistole + overlay text/vektorova grafika
    (cisla castí) jako samostatnou vrstvu. `extract_image` vraci POUZE base JPEG
    bez overlay — cisla by byla ztracena. `get_pixmap(clip=rect)` renderuje
    sektor stranky vcetne vsech vrstev.
    """
    doc = pymupdf.open(pdf_path)
    image_map: dict[int, str] = {}
    RENDER_DPI = 170  # dostatecne pro kvalitu, zvladnutelny file size

    q_per_page: dict[int, list[RawQuestion]] = {}
    for rq, _ in questions:
        q_per_page.setdefault(rq.page_num, []).append(rq)

    for page_num, qs in q_per_page.items():
        page = doc[page_num - 1]
        images = page.get_images(full=True)
        if not images:
            continue

        # Dedupe image rects (PyMuPDF can return duplicates)
        seen_rects: set[tuple[int, int, int, int]] = set()
        img_rects: list[pymupdf.Rect] = []
        for img in images:
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception:
                rects = []
            for r in rects:
                key = (int(r.x0), int(r.y0), int(r.x1), int(r.y1))
                if key not in seen_rects:
                    seen_rects.add(key)
                    img_rects.append(r)

        if not img_rects:
            continue

        qs_sorted = sorted(qs, key=lambda r: r.marker_top)
        used: set[int] = set()
        for i, rq in enumerate(qs_sorted):
            q_top = rq.marker_top
            next_top = qs_sorted[i + 1].marker_top if i + 1 < len(qs_sorted) else page.rect.height + 100
            for j, img_rect in enumerate(img_rects):
                if j in used:
                    continue
                if q_top - 5 <= img_rect.y0 <= next_top:
                    # Filename = q<pdf_number>.png (prehlednejsi nez hash)
                    out = IMAGES_DIR / f"q{rq.pdf_number}.png"
                    try:
                        # Vyrenderuj vyrez stranky vcetne overlay (cisla, anotace)
                        # Padding kolem image bbox pro zachyceni blizkych anotaci
                        pad = 6
                        clip = pymupdf.Rect(
                            max(0, img_rect.x0 - pad),
                            max(0, img_rect.y0 - pad),
                            min(page.rect.width, img_rect.x1 + pad),
                            min(page.rect.height, img_rect.y1 + pad),
                        )
                        zoom = RENDER_DPI / 72.0
                        mat = pymupdf.Matrix(zoom, zoom)
                        pix = page.get_pixmap(clip=clip, matrix=mat, alpha=False)
                        pix.save(str(out))
                        # Optionalne optimalizovat pres Pillow (menej bytes)
                        try:
                            with Image.open(out) as im:
                                im.save(out, "PNG", optimize=True)
                        except Exception:
                            pass
                        image_map[rq.pdf_number] = f"images/q{rq.pdf_number}.png"
                        used.add(j)
                        log.info(f"  Q{rq.pdf_number}: rendered {out.name} ({out.stat().st_size // 1024} KB)")
                        break
                    except Exception as e:
                        log.warning(f"  Q{rq.pdf_number}: chyba renderovani: {e}")
    doc.close()
    return image_map


# ----------------------------- Main -----------------------------

def main():
    DATA_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    if not PDF_PATH.exists():
        console.print(f"[red]PDF nenalezeno: {PDF_PATH}[/red]")
        sys.exit(1)

    console.rule("[bold green]Parsuji PDF MV ČR")
    console.print(f"Zdroj: [cyan]{PDF_PATH.name}[/cyan]")

    parsed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    questions: list[Question] = []
    unparsed: list[UnparsedQuestion] = []

    with pdfplumber.open(PDF_PATH) as pdf:
        console.print(f"Stránek: [bold]{len(pdf.pages)}[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            t = progress.add_task("Segmentace otázek…", total=1)
            raw_questions = parse_pages(pdf)
            progress.update(t, completed=1)

        console.print(f"Nalezeno surových otázek: [bold]{len(raw_questions)}[/bold]")

        # Image extraction (PyMuPDF — separate pass)
        console.rule("[bold]Extrakce obrázků")
        image_map = extract_images_for_questions(PDF_PATH, raw_questions)
        console.print(f"Otázek s obrázkem: [bold]{len(image_map)}[/bold]")

        # Build final questions
        console.rule("[bold]Detekce správných odpovědí")
        for rq, gray_rects in raw_questions:
            q_text = rq.question_text()
            # Sanity: must have all 3 options
            missing = [k for k in ("A", "B", "C") if not rq.options[k]]
            if missing:
                unparsed.append(UnparsedQuestion(
                    pdf_number=rq.pdf_number,
                    source_page=rq.page_num,
                    raw_text=q_text + " | OPTIONS: " + str({k: rq.option_text(k) for k in "ABC"}),
                    reason=f"Chybějící varianty: {missing}",
                ))
                continue

            correct = detect_correct(rq, gray_rects)
            if correct is None:
                unparsed.append(UnparsedQuestion(
                    pdf_number=rq.pdf_number,
                    source_page=rq.page_num,
                    raw_text=q_text,
                    reason="Nedetekováno šedé podbarvení žádné varianty",
                ))
                continue

            opt_a, opt_b, opt_c = rq.option_text("A"), rq.option_text("B"), rq.option_text("C")
            qid = hash_id(q_text, opt_a, opt_b, opt_c)
            try:
                q = Question(
                    id=qid,
                    pdf_number=rq.pdf_number,
                    section=section_for_page(rq.page_num),
                    question=q_text,
                    image=image_map.get(rq.pdf_number),
                    options=Options(A=opt_a, B=opt_b, C=opt_c),
                    correct=correct,
                    source_page=rq.page_num,
                    source_pdf=PDF_PATH.name,
                    parsed_at=parsed_at,
                )
                questions.append(q)
            except Exception as e:
                unparsed.append(UnparsedQuestion(
                    pdf_number=rq.pdf_number,
                    source_page=rq.page_num,
                    raw_text=q_text,
                    reason=f"Pydantic validace: {e}",
                ))

    # Write JSON
    out_q = DATA_DIR / "questions.json"
    out_q.write_text(
        json.dumps([q.model_dump() for q in questions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    out_u = DATA_DIR / "unparsed.json"
    out_u.write_text(
        json.dumps([u.model_dump() for u in unparsed], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    console.rule("[bold green]Hotovo")
    console.print(f"✅ Zapsáno: [bold]{len(questions)}[/bold] otázek → {out_q}")
    console.print(f"📷 S obrázkem: [bold]{sum(1 for q in questions if q.image)}[/bold]")
    console.print(f"⚠️  Nedořešeno: [bold yellow]{len(unparsed)}[/bold yellow] → {out_u}")

    # Section breakdown
    by_section: dict[str, int] = {}
    for q in questions:
        by_section[q.section or "unknown"] = by_section.get(q.section or "unknown", 0) + 1
    console.print("\n[bold]Rozložení podle oblasti:[/bold]")
    for sec, n in sorted(by_section.items()):
        console.print(f"  {sec:<25} {n:>4}")


if __name__ == "__main__":
    main()
