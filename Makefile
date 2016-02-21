build: clean
	python setup.py -q sdist bdist_wheel

clean:
	rm -fr build dist *.egg-info .coverage htmlcov

very-clean: clean
	rm -fr .eggs .cache
	find . -name '*.pyc' | xargs rm -f

install:
	pip install -e .

install-dev:
	pip install pep8

test-release: build test
	twine upload -r pypitest dist/*

release: build test
	twine upload dist/*

test:
	pep8 setup.py humu_download

.PHONY: build clean very-clean install install-dev test-release release test
