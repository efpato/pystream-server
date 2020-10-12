SRC := pystream-server.py


# CODE: CHECKS
check-isort:
	isort --check-only $(SRC)

check-black:
	black --check $(SRC)

check-pylint:
	pylint $(SRC)

check-mypy:
	rm -rf .mypy_cache
	mypy --config-file=pyproject.toml $(SRC)

check: check-isort check-black check-mypy check-pylint


# CODE: FORMAT
isort:
	isort $(SRC)

black:
	black $(SRC)

format: isort black
