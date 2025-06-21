SHELL=/usr/bin/env bash

# Conda environment name and Python version
ENV_NAME = dra
PYTHON_VERSION = 3.11

# Default goal
.DEFAULT_GOAL := help

# 🛠️ Remove Conda environment
.PHONY: clean
clean:
	conda remove -y --name $(ENV_NAME) --all

# 🛠️ Install dependencies using Poetry
.PHONY: install
install:
	@echo "Installing dependencies"
	pip install poetry
	pip install 'markitdown[all]'
	pip install "browser-use[memory]"==0.1.48

	# install playwright
	pip install playwright
	playwright install chromium --with-deps --no-shell

	# install dependencies
	poetry install

	# install xlrd
	pip install xlrd==2.0.1

install-requirements:
	@echo "Installing dependencies"
	pip install poetry
	pip install 'markitdown[all]'
	pip install "browser-use[memory]"==0.1.48

	# install playwright
	pip install playwright
	playwright install chromium --with-deps --no-shell

	# install dependencies
	pip install -r requirements.txt

	# install xlrd
	pip install xlrd==2.0.1

# 🌐 Install Web UI dependencies
.PHONY: install-webui
install-webui:
	@echo "Installing Web UI dependencies"
	pip install -r requirements_webui.txt
	@echo "Web UI dependencies installed successfully!"

# 🚀 Start Web UI (Streamlit)
.PHONY: webui
webui:
	@echo "Starting DeepResearchAgent Web UI..."
	cd web_ui && python launcher.py --streamlit

# 🚀 Start Web UI (Full-stack)
.PHONY: webui-full
webui-full:
	@echo "Starting DeepResearchAgent Full-stack Web UI..."
	cd web_ui && python launcher.py --full-stack

# 🔧 Start API server only
.PHONY: api
api:
	@echo "Starting DeepResearchAgent API server..."
	cd web_ui && python launcher.py --api

# 🛠️ Update dependencies using Poetry
.PHONY: update
update:
	poetry update

# 🛠️ Show available Makefile commands
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  make create       - Create Conda environment and install Poetry"
	@echo "  make activate     - Show activation command"
	@echo "  make clean        - Remove Conda environment"
	@echo "  make install      - Install dependencies using Poetry"
	@echo "  make update       - Update dependencies using Poetry"
	@echo ""
	@echo "Web UI commands:"
	@echo "  make install-webui - Install Web UI dependencies"
	@echo "  make webui        - Start Streamlit Web UI"
	@echo "  make webui-full   - Start Full-stack Web UI (API + Streamlit)"
	@echo "  make api          - Start API server only"
