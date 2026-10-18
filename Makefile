SHELL := /bin/bash

.PHONY: help setup run test lint

help:
	@echo "setup - create venv and install requirements"
	@echo "run   - start the Streamlit app"
	@echo "test  - byte-compile the Python files"
	@echo "lint  - reserved for future lint tooling"

setup:
	python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

run:
	streamlit run app.py

test:
	python3 -m compileall .

lint:
	@echo "No dedicated lint command is configured yet."
