#!/bin/bash

./scripts/validate_open_api_file_up_to_date.sh
./scripts/verify_open_api_client_is_up_to_date.sh
isort .
black .
flake8 .
pycodestyle .
# Let mypy read targets from mypy.ini (avoids duplicate module names like src.package vs package)
mypy .
yamllint . --no-warnings