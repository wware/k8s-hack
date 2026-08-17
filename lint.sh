#!/bin/bash -e

uv run ruff check .
uv run ruff check --fix . && uv run ruff format .
uv run mypy --strict .
uv run pytest .
