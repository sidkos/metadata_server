# Project overview
A small, production-ready example of a REST API server with an OpenAPI schema, a generated low‑level client, and a higher‑level testing client. It demonstrates API design, validation, JWT auth, containerization, CI/CD, and tests (unit and component).

- Server endpoints: `POST /api/users/`, `GET /api/users/{id}/`, `GET /api/users/`, `GET /api/health/`.
- Persists users in PostgreSQL with input validation and clear error responses.

# Deliverables and separation
- metadata_server (this repository): Django REST Framework server and Docker image.
- metadata_client: Generated Python client from the server’s OpenAPI (thin, endpoint‑oriented). Used in unit tests.
- dp-client: Higher‑level Python client intended for component tests. It composes the generated metadata_client plus optional DB checks via its own DB drivers.

Notes on separation and SDLC:
- metadata_server, metadata_client, and dp-client should each have an independent SDLC: separate repositories, versioning, release pipelines, and artifacts.
- Best practice: split dp-client into its own repository and manage it there independently.
- Best practice: publish both metadata_client and dp-client to a package registry (e.g., PyPI, GH Packages, CodeArtifact) and consume them by version in downstream projects.

# Versioning status
- Versioning of published deliverables is not yet implemented here; currently we use on‑the‑fly builds or "latest" artifacts during CI and local development.
- Should be introduced: semantic versioning for metadata_server, metadata_client, and dp-client, published releases, and version pinning in consumers for reproducible builds.

# Technologies used and why
- Django + Django REST Framework: rapid API development, serializers, validation, permissions.
- SimpleJWT (DRF): standard JWT‑based authentication.
- drf-spectacular: OpenAPI generation for accurate client generation.
- PostgreSQL: reliable relational database with first‑class support on GitHub Actions.
- Docker: consistent runtime for the server.
- GitHub Actions: automated CI/CD with reusable workflows.

When to use what:
- Use metadata_client for thin, OpenAPI‑aligned calls (used in unit tests).
- Use dp-client for higher‑level test flows including optional DB verification (used in component tests).

# API surface (summary)
- POST /api/users/ — Create a user
- GET /api/users/{id}/ — Retrieve user by ID
- GET /api/users/ — List all user IDs
- GET /api/health/ — Public health check (no auth)

Validation rules:
- id: Valid Israeli ID (checksum validated)
- phone: International format starting with `+`
- name: Required
- address: Required

# Authentication (JWT)
Approach: JWT‑only API auth using Django REST Framework + SimpleJWT.
- Global permission is IsAuthenticated (all endpoints require a token) except `/api/health/`.
- OpenAPI advertises global `bearerAuth` security scheme.

Usage flow:
- Obtain token at `POST /api/token/` with JSON `{"username":"<u>", "password":"<p>"}` → `{"access","refresh"}`.
- Call protected endpoints with header `Authorization: Bearer <access>`.
- Refresh access tokens at `POST /api/token/refresh/` with `{"refresh"}`.

References:
- DRF: https://www.django-rest-framework.org/
- SimpleJWT: https://django-rest-framework-simplejwt.readthedocs.io/en/latest/
- drf-spectacular: https://drf-spectacular.readthedocs.io/en/latest/

# Logging in the server
- Uses Django’s logging framework. By default, logs go to stdout/stderr (captured by Docker and CI logs).
- You can tune the LOGGING dict in settings.py for JSON output, correlation IDs, and routing to a centralized sink via container stdout.
- Defaults provide level‑tagged lines suitable for `docker compose logs` or `docker logs <container>`.

# Requirements files and why they differ
Different contexts need different dependency sets. This repository intentionally separates them:

- requirements.txt (server runtime): dependencies to run the Django app in production or a container. Typical libs: Django, DRF, JWT, PostgreSQL driver, drf‑spectacular.

- dp-client/requirements.txt (dp‑client runtime): dependencies needed to use dp-client as a standalone package, including its DB driver(s) for component tests (e.g., psycopg2-binary). Keeps client usage decoupled from server dependencies.

- requirements-build-client.txt (client build toolchain): tools required to generate and build the OpenAPI client(s). For example:
  - openapi-python-client — generates the metadata_client from the OpenAPI schema.
  - poetry — builds the Python packages (e.g., dp-client).
  - typer and click — CLI dependencies some tooling relies on.
  Use case: CI jobs or local scripts that generate and build the client packages without installing full dev tooling.

- requirements-dev.txt (development toolchain): editor/test/quality tools for contributors:
  - Linters/formatters: black, flake8, isort, yamllint.
  - Typing: mypy, django-stubs, djangorestframework-stubs.
  - Testing: pytest, pytest-django.
  - Release tooling: python-semantic-release (future use when versioning is introduced).
  - Utilities: dotenv for loading `.env` in tests and scripts.
  Use case: local development and CI quality gates.

This separation ensures minimal, context‑appropriate installs. For example, a developer running only the server doesn’t need OpenAPI generators; a test runner using only dp-client doesn’t need the entire server stack.

# Local development and examples
## .env example
```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
METADATA_PORT=8000
METADATA_HOST=localhost
TEST_USERNAME=test_username
TEST_PASSWORD=1qazxsw@
```

## Install requirements
You can install everything needed for this repository in one go:

```
./scripts/install_all_requirements.sh
```

Tip: run inside a virtual environment first:
```
python -m venv .venv && source .venv/bin/activate
```

Or pick the set that matches your task:
- Server runtime:
  pip install -r requirements.txt
- dp‑client runtime:
  pip install -r dp-client/requirements.txt
- Client build toolchain (for generating/building clients):
  pip install -r requirements-build-client.txt
- Full development toolchain (linting, typing, testing, etc.):
  pip install -r requirements-dev.txt

## Run locally with docker‑compose (recommended)
```
docker compose up --build
# Server becomes available at:
# http://localhost:8000/api/health/
```

Healthcheck example:
```
curl http://localhost:8000/api/health/
```

## Client builds and local install
Build and install both clients locally when developing:
```
# Build and install the generated OpenAPI client (metadata_client)
./scripts/build_and_install_open_api_client.sh

# Build and install dp-client (will build metadata_client first; installs without fetching deps)
./scripts/build_and_install_dp_client.sh
```

## Tests
- Unit tests (use metadata_client, typically with compose up):
  pytest tests/unit -s -v
- Component tests (use dp-client and verify DB persistence):
  # Optionally enable fallback if your .env uses POSTGRES_HOST=db and you're outside compose
  export POSTGRES_ALLOW_LOCAL_FALLBACK=true

  ./scripts/build_and_install_dp_client.sh
  pytest tests/component -s -v

# OpenAPI and clients
- We validate that the OpenAPI schema is up‑to‑date and that the generated client is not drifting using repository scripts (see scripts/):
  - scripts/validate_open_api_file_up_to_date.sh
  - scripts/verify_open_api_client_is_up_to_date.sh
- metadata_client mirrors the API one‑to‑one and is ideal for unit tests and simple integrations.
- dp-client composes:
  - a factory for constructing authenticated/unauthenticated metadata_client instances
  - separated API wrappers (e.g., UsersAPI, HealthAPI)
  - a DB helper (PGDBClient) with driver‑based design (Postgres provided), fully decoupled from Django ORM.

# CI/CD overview
Entry point: CI‑CD Pipelines interface — https://github.com/sidkos/metadata_server/actions/workflows/ci_cd.yml

Pipeline summary:
- Quality gates:
  - Lint/format
  - mypy with Django plugin and stubs configuration
  - OpenAPI validation and client drift checks
  - Unit tests (reusable workflow analogous to unit_tests_on_docker.yml)
- Build server image:
  - Builds and pushes ghcr.io/<owner>/metadata_server:latest.
- Component tests (reusable component_tests.yml):
  - Spins up a GitHub Actions PostgreSQL service.
  - Pulls the server image built in the previous step and runs it.
  - Waits for `/api/health/` readiness.
  - Builds/installs dp-client on the runner and executes pytest against tests/component.

# Notes on release strategy
- Current workflows build and use the latest images and locally built clients; version pinning and artifact publishing are not yet implemented.
- Recommended next steps:
  - Introduce semantic versioning for all deliverables.
  - Publish metadata_client and dp-client to a registry and pin versions in tests and downstream projects.
  - Keep dp-client in a separate repository with its own SDLC, releases, and changelog.
