"""Generátor markdown souborů pro vysvětlení v Claude Code."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = ROOT / "exports"


SECTION_LABEL = {
    "pravo": "Právo",
    "provadeci_predpisy": "Prováděcí předpisy",
    "jine_predpisy": "Jiné předpisy",
    "nauka_o_zbranich": "Nauka o zbraních a střelivu",
    "zdravotni_minimum": "Zdravotnické minimum",
}


def _format_question_block(q: dict, my_answer: str | None = None, note: str = "") -> str:
    img = ""
    if q.get("image"):
        img_abs = (ROOT / q["image"]).as_posix()
        img = f"\n![obrázek otázky]({img_abs})\n"
    correct = q["correct"]
    correct_text = q["options"][correct]
    section = SECTION_LABEL.get(q.get("section") or "", "—")
    parts = [
        f"### Otázka č. {q['pdf_number']} ({section})",
        f"**Hash:** `{q['id']}`",
        f"**Strana v PDF:** {q.get('source_page', '?')}",
        "",
        q["question"],
        img,
        "**Možnosti:**",
        f"- A) {q['options']['A']}",
        f"- B) {q['options']['B']}",
        f"- C) {q['options']['C']}",
        "",
        f"**Správná odpověď podle PDF MV ČR:** {correct} — {correct_text}",
    ]
    if my_answer:
        ok = "✅ správně" if my_answer == correct else "❌ špatně"
        parts.append(f"**Moje odpověď:** {my_answer} ({ok})")
    if note.strip():
        parts.append(f"**Moje poznámka:** {note.strip()}")
    return "\n".join(parts)


PROMPT_TEMPLATE = """\
# Žádost o vysvětlení testových otázek ZOZ (zbrojní průkaz)

Připravuji se na zkoušku odborné způsobilosti k vydání zbrojního průkazu podle:
- **Zákona č. 90/2024 Sb.**, o zbraních a střelivu
- **Nařízení vlády č. 238/2025 Sb.**, o provádění zkoušek

Níže přikládám otázky, kterým úplně nerozumím nebo si nejsem jistý správnou odpovědí.

## Co od tebe potřebuji u každé otázky
1. **Vysvětli laicky**, proč je správná odpověď taková, jaká je.
2. **Cituj konkrétní paragraf** zákona č. 90/2024 Sb. (případně NV č. 238/2025 Sb. nebo jiného předpisu).
3. **Odkaz** na oficiální zdroj (zakonyprolidi.cz, mv.gov.cz) — pokud možno přímo na §.
4. **Proč jsou ostatní odpovědi špatně** — krátce u každé.
5. **Mnemotechnická pomůcka** nebo příklad ze života pro zapamatování.

Pokud máš podezření, že odpověď v PDF MV ČR je zastaralá nebo chybná (nesoulad s aktuálním zněním zákona), upozorni mě.

---

"""


def export_questions(
    questions: list[dict],
    *,
    my_answers: dict[str, str] | None = None,   # qid -> chosen
    notes: dict[str, str] | None = None,         # qid -> note
    filename_hint: str = "explain",
) -> Path:
    EXPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    n = len(questions)
    out = EXPORT_DIR / f"{filename_hint}_{n}q_{ts}.md"

    parts = [PROMPT_TEMPLATE]
    parts.append(f"_Vyexportováno {datetime.now().strftime('%Y-%m-%d %H:%M')}, počet otázek: {n}._\n")
    for q in questions:
        my = (my_answers or {}).get(q["id"])
        note = (notes or {}).get(q["id"], "")
        parts.append(_format_question_block(q, my_answer=my, note=note))
        parts.append("\n---\n")

    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def export_single(q: dict, my_answer: str | None = None, note: str = "") -> Path:
    return export_questions(
        [q],
        my_answers={q["id"]: my_answer} if my_answer else None,
        notes={q["id"]: note} if note else None,
        filename_hint=f"q{q['pdf_number']}",
    )
