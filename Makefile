FLAKE_EXCLUDES=E401,F401,W503,F841,E266,E402,E722,C416,B001,B008,E501
BANDIT_EXCLUDES=B101,B105,B110,B307,B310,B311

lint_python:
	shopt -s globstar && pyupgrade --py36-plus **/*.py
	bandit --recursive --skip $(BANDIT_EXCLUDES) .
	black -l 79 .
	# codespell --ignore-words-list="hass" custom_components
	flake8 . --count --ignore $(FLAKE_EXCLUDES) \
                  --max-complexity=15 --max-line-length=79 \
                  --show-source --statistics
	mypy --show-error-codes --ignore-missing-imports --install-types \
              --non-interactive \
              --disable-error-code no-redef \
              . 
	safety check


test:
	pytest tests/


install_requirements:
	pip install --upgrade pip wheel
	pip install bandit black codespell flake8 flake8-2020 flake8-bugbear \
                  flake8-comprehensions isort mypy pytest pyupgrade safety
