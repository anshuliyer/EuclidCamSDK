# ============================================================
#  firmware/python — Makefile
# ============================================================

SHELL  := /bin/bash
PYTHON := python3
ENTRY  := camera.py

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "firmware/python"
	@echo ""
	@echo "  make run    launch camera (foreground)"
	@echo "  make check  syntax-check all .py files"
	@echo "  make lint   flake8"
	@echo "  make clean  remove __pycache__, temp.jpg"

.PHONY: run
run:
	$(PYTHON) $(ENTRY)

.PHONY: check
check:
	@find . -name "*.py" | sort | while read f; do \
		$(PYTHON) -c "import ast; ast.parse(open('$$f').read())" \
			&& echo "  ok  $$f" || echo "  ERR $$f"; \
	done

.PHONY: lint
lint:
	flake8 . --max-line-length=100 \
		--exclude=__pycache__,.venv \
		--extend-ignore=E501,W503

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f temp.jpg
