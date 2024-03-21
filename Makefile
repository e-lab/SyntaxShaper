$(VERBOSE).SILENT:
.DEFAULT_GOAL := help

.PHONY: install
install: 
	python setup.py install

.PHONY: lint
lint:
	echo "isort:"
	echo "======"
	python3 -m isort --profile=black --line-length=120 .
	echo
	echo "black:"
	echo "======"
	python3 -m black --line-length=120 .

.PHONY: upload 
upload:
	rm -rf dist/ *.egg-info/ build/ && python3 -m build && python3 setup.py sdist && python3 -m twine upload dist/*   

.PHONY: clean
clean: 
	rm -rf dist/ *.egg-info/ build/

.PHONY: commit
commit: 
	make clean && git add . && git commit -m "update" && git push upstream main 