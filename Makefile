$(VERBOSE).SILENT:
.DEFAULT_GOAL := help

.PHONY: install
install: ## Installs all required dependencies and dependencies for local development
	python setup.py install

.PHONY: lint
lint: ## lints the codebase
	echo "isort:"
	echo "======"
	python3 -m isort --profile=black --line-length=120 .
	echo
	echo "black:"
	echo "======"
	python3 -m black --line-length=120 .