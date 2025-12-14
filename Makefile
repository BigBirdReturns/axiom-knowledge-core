.PHONY: help install policy compile validate tutor test pack-audit pack-runtime

help:
	@echo "Targets:"
	@echo "  install   Install editable packages"
	@echo "  policy    Enforce source input contract under sources/"
	@echo "  compile   Compile sources/ into compiled/ using AXM via AXIOM Knowledge Core"
	@echo "  validate  Run unit tests for AXIOM Knowledge Core"
	@echo "  tutor     Run Streamlit tutor (uses TUTOR_COMPILED_DIR if set)"
	@echo "  test      Run all tests"
	@echo "  pack-audit  Build audit pack zips under dist/"
	@echo "  pack-runtime Build runtime pack zips under dist/"

install:
	python -m pip install -U pip
	python -m pip install -e packages/axm
	python -m pip install -e packages/axiom-knowledge-core
	python -m pip install -r apps/kid_local_tutor/requirements.txt

policy:

	python scripts/ci_sources_gate.py
compile:
	ak compile --sources sources --out compiled

validate:
	python -m pytest -q packages/axiom-knowledge-core apps/kid_local_tutor

tutor:
	python -m streamlit run apps/kid_local_tutor/app.py


test:
	python -m pytest -q

pack-audit:
	python scripts/pack.py build --pack first-aid-fm21-11 --flavor audit

pack-runtime:
	python scripts/pack.py build --pack first-aid-fm21-11 --flavor runtime
