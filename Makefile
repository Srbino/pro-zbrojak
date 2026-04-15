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

.PHONY: help install parse run test test-ui mindmap lint clean

help:
	@echo "Pro Zbrojak — dostupne prikazy:"
	@echo "  make install    vytvori venv a nainstaluje zavislosti"
	@echo "  make run        spusti aplikaci (http://127.0.0.1:8080)"
	@echo "  make test       vsechny testy"
	@echo "  make test-ui    jen UI E2E testy"
	@echo "  make mindmap    vygeneruje QUESTIONS_MINDMAP.md"
	@echo "  make lint       ruff check + format"
	@echo "  make clean      smaze DB a cache (user-local)"
	@echo ""
	@echo "Pro maintainery:"
	@echo "  make parse      regeneruje data/questions.json z PDF MV CR"

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip

install: $(VENV)/bin/python
	$(PIP) install --quiet -e ".[dev]"
	$(PY) -m playwright install --with-deps chromium 2>/dev/null || \
		$(PY) -m playwright install chromium
	@echo "OK — spustite: make run"

parse: $(VENV)/bin/python
	@test -f MV-Soubor_testovych_otazek_*.pdf || (echo "CHYBA: PDF soubor chybi. Viz README (sekce 'Stazeni PDF')." && exit 1)
	$(PY) parse_pdf.py

run:
	@test -f data/questions.json || (echo "CHYBA: data/questions.json chybi v repu. Zkontroluj klon." && exit 1)
	$(PY) app.py

test:
	$(PY) -m pytest

test-ui:
	$(PY) -m pytest tests/test_ui_e2e.py tests/test_ui_interactions.py tests/test_ui_icons.py tests/test_responsive.py tests/test_responsive_gallery.py tests/test_images.py -v

mindmap:
	$(PY) scripts/generate_mindmap.py

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
