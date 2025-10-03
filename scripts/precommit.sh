#!/bin/bash

isort .
black .
flake8 .
pycodestyle .
PYTHONPATH=src mypy .
yamllint . --no-warnings