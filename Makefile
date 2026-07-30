# Makefile — uzivatelske prikazy pro Pro Zbrojak.
# Pouziti:
#   make install   — vytvori venv + nainstaluje zavislosti
#   make run       — spusti aplikaci (http://127.0.0.1:8080)
#   make test      — pusti testy (pytest)
#   make test-ui   — spusti jen E2E UI testy (Playwright)
#   make mindmap   — vygeneruje QUESTIONS_MINDMAP.md
#   make clean     — smaze DB a cache
#
# Pro maintainery (regenerace obsahu z noveho PDF MV CR):
#   make parse     — naparsuje MV-Soubor_testovych_otazek_*.pdf → data/questions.json + images/

PYTHON ?= python3
VENV   := .venv
PIP    := $(VENV)/bin/pip
PY     := $(VENV)/bin/python

.PHONY: help install parse run test test-ui test-data mindmap validate-zakon \
        law-links traps prirucka prirucka-chybi podcast klic okruhy studium \
        lint clean clean-all

help:
	@echo "Pro Zbrojak — dostupne prikazy:"
	@echo ""
	@echo " Provoz"
	@echo "  make install    vytvori venv a nainstaluje zavislosti"
	@echo "  make run        spusti aplikaci (http://127.0.0.1:8080)"
	@echo "  make test       vsechny testy"
	@echo "  make test-ui    jen UI E2E testy"
	@echo "  make lint       ruff check + format"
	@echo "  make clean      smaze DB a cache (user-local)"
	@echo ""
	@echo " Studijni materialy (docs/studium/)"
	@echo "  make studium    vygeneruje vsechno najednou"
	@echo "  make prirucka   otazka + odpoved + paragraf + vyklad"
	@echo "  make podcast    jen spravne odpovedi, podklad k predcitani"
	@echo "  make okruhy     tematicke okruhy podle cleneni zakona"
	@echo "  make klic       soupis cislo -> spravne pismeno"
	@echo ""
	@echo " Pro maintainery (vyzaduje zdrojove PDF v docs/, viz README)"
	@echo "  make parse      regeneruje data/questions.json + images/ z PDF MV CR"
	@echo "  make test-data  overi katalog proti PDF (odpovedi, textace, obrazky)"
	@echo "  make validate-zakon  overi otazky proti zneni zak. 90/2024 Sb."
	@echo "  make law-links       pregeneruje odkazy do e-Sbirky (chodi na sit)"
	@echo "  make traps           pregeneruje seznam chytaku z katalogu"
	@echo "  make mindmap         vygeneruje QUESTIONS_MINDMAP.md"

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip

install: $(VENV)/bin/python
	$(PIP) install --quiet -e ".[dev]"
	$(PY) -m playwright install --with-deps chromium 2>/dev/null || \
		$(PY) -m playwright install chromium
	@echo "OK — spustite: make run"

parse: $(VENV)/bin/python
	@test -f docs/MV-Soubor_testovych_otazek_*.pdf || \
		(echo "CHYBA: docs/MV-Soubor_testovych_otazek_*.pdf chybi. Viz README, sekce 'Zdrojove PDF'." && exit 1)
	$(PY) parse_pdf.py

# Overi katalog proti zdrojovemu PDF: spravne odpovedi, textace za pismeny
# a uplnost obrazku. Bez PDF se tyhle testy PRESKOCI — proto samostatny cil,
# ktery na jeho nepritomnost upozorni.
test-data:
	@test -f docs/MV-Soubor_testovych_otazek_*.pdf || \
		(echo "CHYBA: bez docs/MV-Soubor_*.pdf se katalog proti zdroji overit neda." && exit 1)
	$(PY) -m pytest tests/test_all_answers_vs_pdf.py tests/test_option_mapping_vs_pdf.py \
		tests/test_images_vs_pdf.py tests/test_questions_integrity.py -v

run:
	@test -f data/questions.json || (echo "CHYBA: data/questions.json chybi v repu. Zkontroluj klon." && exit 1)
	$(PY) app.py

test:
	$(PY) -m pytest

test-ui:
	$(PY) -m pytest tests/test_ui_e2e.py tests/test_ui_interactions.py tests/test_ui_icons.py tests/test_responsive.py tests/test_responsive_gallery.py tests/test_images.py -v

mindmap:
	$(PY) scripts/generate_mindmap.py

# Lexikalni overeni odpovedi proti plnemu zneni zakona (vyzaduje pdftotext/poppler).
# Bez venv — skript vystaci se standardni knihovnou.
validate-zakon:
	python3 scripts/validate_vs_zakon.py --all

# Pregeneruje data/law_refs.json — odkazy z otazek na ustanoveni v e-Sbirce MV CR.
# Chodi na sit (overuje kazdy odkaz proti otevrenym datum), spousti se zridka.
law-links:
	python3 scripts/gen_law_links.py

# Pregeneruje data/traps.json — otazky, kde se distraktor lisi o kousek.
# Cte jen katalog, na sit nechodi a zneni zakona nepotrebuje.
traps:
	python3 scripts/gen_traps.py

# Pregeneruje studijni prirucku do docs/. Vyklady se berou z data/vyklady.json
# a NEPREPISUJI se — markdown je odvozeny soubor, editovat se ma ten JSON.
prirucka:
	python3 scripts/gen_prirucka.py --all --out docs/studium/prirucka.md
	python3 scripts/gen_prirucka.py --all --split docs/studium/prirucka/

# Otazky, kterym vyklad zatim chybi — podklad pro dalsi kolo psani.
prirucka-chybi:
	python3 scripts/gen_prirucka.py --all --missing --out docs/studium/prirucka-chybi.md

# Podklad k predcitani: zadani, spravna odpoved a zakon. Bez nespravnych
# moznosti — pri poslechu se snadno zapamatuje zrovna ta spatna varianta.
podcast:
	python3 scripts/gen_prirucka.py --all --jen-spravne --out docs/studium/podcast.md
	python3 scripts/gen_prirucka.py --all --jen-spravne --only-law --out docs/studium/podcast-se-zakonem.md
	python3 scripts/gen_prirucka.py --all --jen-spravne --split docs/studium/podcast/

# Soupis cislo -> spravne pismeno, ke kontrole proti oficialni prirucce.
klic:
	python3 scripts/gen_prirucka.py --all --klic --out docs/studium/klic-odpovedi.md

# Tematicke okruhy — otazky seskupene podle toho, co v zakone resi.
# Cleneni bere ze zakona (CAST -> HLAVA -> Dil), nevymysli si ho.
# Vyzaduje data/zakon_90_2024.txt (neni v repu, viz README).
okruhy:
	python3 scripts/gen_okruhy.py

# Vsechny studijni materialy najednou.
studium: prirucka podcast klic okruhy
	@echo "Hotovo — docs/studium/"

lint:
	$(VENV)/bin/ruff check . || true
	$(VENV)/bin/ruff format . || true

clean:
	# Smaze jen user-local artefakty. questions.json a images/ jsou soucasti repa.
	rm -rf data/stats.db data/unparsed.json
	rm -rf exports/*.md
	rm -rf logs/*.log
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache tests/screenshots
	@echo "Clean done."

clean-all: clean
	rm -rf $(VENV)
	@echo "Removed venv."
