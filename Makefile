FLAKE_EXCLUDES=B001,W503,E722
# B001 Do not use bare `except:`, it also catches unexpected events like memory errors, interrupts, system exit, and so on.  Prefer `except Exception:`.  If you're sure what you're doing, be explicit and write `except BaseException:`.
# W503 line break before binary operator
# E722 do not use bare 'except'

BANDIT_EXCLUDES=B101,B105,B110,B310,B311
PIP:=pip3

lint_python:
	-shopt -s globstar && pyupgrade --py36-plus **/*.py
	-autoflake8 -i -r test* custom_components
	bandit --recursive --skip $(BANDIT_EXCLUDES) .
	black -l 88 .
	# codespell --ignore-words-list="hass" custom_components
	flake8 .
	mypy --show-error-codes --ignore-missing-imports --install-types \
              --non-interactive \
              custom_components test*
	# safety check
	-mdformat --wrap 75 README.md --number


prodtest:
	python3 ./testEnedis.py |& tee prodtest.log

test:
	pytest -sv tests/


install_requirements:
	$(PIP) install --upgrade pip wheel
	$(PIP) install bandit black codespell flake8 flake8-2020 flake8-bugbear \
                  flake8-comprehensions isort mypy pytest pyupgrade safety \
                  autoflake8 mdformat requests_mock mock packaging
	$(PIP) install -r requirements.txt

setup_precommit:
	$(PIP) install --upgrade pip pre-commit tox
	pre-commit install
