.PHONY: install dev lint fmt test run run-http smoke inspect diagrams docker-build docker-run clean

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
IMAGE ?= roshan-harf-mcp:latest

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install -e .

dev: $(VENV)
	$(PIP) install -e ".[dev]"
	$(PIP) install diagrams

lint:
	$(VENV)/bin/ruff check src tests

fmt:
	$(VENV)/bin/ruff check --fix src tests
	$(VENV)/bin/ruff format src tests

test:
	$(PY) -m pytest -q

smoke:
	$(PY) scripts/smoke_test.py

inspect:
	$(PY) examples/inspect_server.py

run:
	$(PY) -m roshan_harf_mcp

run-http:
	$(PY) -m roshan_harf_mcp --transport streamable-http --host 0.0.0.0 --port 8000

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p 8000:8000 \
		-e ROSHAN_HARF_BASE_URL=$${ROSHAN_HARF_BASE_URL:-https://harf.roshan-ai.ir} \
		-e ROSHAN_HARF_TOKEN=$$ROSHAN_HARF_TOKEN \
		$(IMAGE)
