# dp-client

A higher-level, test-friendly Python client for the Metadata Server, designed for component/end‑to‑end tests. It provides a structured API façade over the server’s endpoints and optional DB checks via driver-based adapters.

- Lives in its own folder (`dp-client/`)
- Manages its own runtime requirements (`dp-client/requirements.txt`)
- Built via Poetry; helper scripts provided

## When to use dp-client
- Use `dp-client` for component tests and higher-level flows (create → verify via API and DB). It provides a stable façade and hides low-level API details.

## Architecture
`DPClient` composes distinct parts with strict separation of concerns:
- MetaDataServerAPIClient — factory‑built HTTP client for the Metadata Server (authenticated or not).
- HealthAPI — methods for `/api/health/`.
- UsersApi — methods for `/api/users/` (create/get/list/update/partial_update/destroy) with strict id immutability enforced by the server. The client injects the path id into PUT bodies if omitted, and rejects PATCH bodies containing `id`.
- PGDBClient — optional Postgres DB helper used in tests to verify persistence and cleanup. It is decoupled from Django ORM and uses driver(s) under `dp_client.db.drivers`.

This design keeps HTTP API usage and DB verification separate, while allowing simple orchestration from tests.

## Installation
Option A: install runtime requirements for dp-client only

```bash
pip install -r dp-client/requirements.txt
```

Option B: build and install the package (recommended for local dev; also used in CI)

```bash
# From repo root
./scripts/build_and_install_dp_client.sh
```

Notes:
- The installer resolves and installs prerequisites automatically, then builds and installs `dp-client` using `pip install --no-deps` to avoid fetching from remote indexes.
- Versioning across deliverables is not implemented yet; current flows use latest/on‑the‑fly builds. Introducing semantic versioning is recommended.

## Configuration
dp-client reads configuration from arguments and environment variables.

API base URL and auth:
- Base URL is passed to `DPClient(base_url=...)`.
- For authenticated usage, pass `token` (a JWT from `POST /api/token/`) and optionally `prefix="Bearer"` if not default.

Database connection (for PGDBClient):
- POSTGRES_HOST
- POSTGRES_PORT
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_ALLOW_LOCAL_FALLBACK (optional, truthy values enable fallback to `localhost` when the host, e.g. `db`, is not resolvable outside Docker networks.)

## Usage examples
Basic (no auth required for health):

```python
from dp_client import DPClient

client = DPClient(base_url="http://localhost:8000")
res = client.HealthAPI.health_check()
print(res.status_code, res.parsed)
```

Authenticated usage (JWT):

```python
import os
from dp_client import DPClient

base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
access_token = os.environ["ACCESS_TOKEN"]  # obtain via POST /api/token/

client = DPClient(base_url=base_url, token=access_token)

# Create a user via API
payload = {"id": "123456782", "name": "Alice", "phone": "+972501234567", "address": "Street 1"}
create_resp = client.UsersApi.create_user(payload)
assert create_resp.status_code == 201
user_id = create_resp.parsed.id

# Verify via API
get_resp = client.UsersApi.get_user(user_id)
assert get_resp.status_code == 200

# Optional: verify in DB and cleanup
if client.PGDBClient is not None:
    db_user = client.PGDBClient.get_user_by_id(user_id)
    assert db_user and db_user["id"] == user_id
    client.PGDBClient.delete_users_by_ids([user_id])
```

Backwards‑compatible helpers (delegating to structured APIs):

```python
from dp_client import DPClient
client = DPClient(base_url="http://localhost:8000", token="<ACCESS_TOKEN>")

# Health
client.health_check()

# Users CRUD
client.create_user({"id": "...", "name": "...", "phone": "+972...", "address": "..."})
client.get_user("<id>")
client.list_users()

# Update (PUT): body must represent the same id as in the path; if omitted, dp-client injects the path id
client.update_user("<id>", {"name": "New", "phone": "+9728...", "address": "..."})

# Partial update (PATCH): must NOT include 'id' in body
client.partial_update_user("<id>", {"address": "Changed"})

# Delete
client.delete_user("<id>")
```

## Using dp-client in component tests
- Component tests in this repo import `DPClient` and use it to call the server and to check the DB (when available).
- If your `.env` uses `POSTGRES_HOST=db` (Docker service name) and you run tests outside Docker, enable safe fallback:

```bash
export POSTGRES_ALLOW_LOCAL_FALLBACK=true
```

- When the database is not reachable, DB‑dependent assertions in tests may be skipped with an explanatory message.

## Requirements
Runtime dependencies for dp-client are declared in:

- `dp-client/requirements.txt` (includes the DB driver for Postgres)

Install them directly, or rely on `./scripts/build_and_install_dp_client.sh` which builds and installs compatible wheels locally.

## Scripts
- `scripts/build_dp_client.sh` — builds the dp-client wheel with Poetry and syncs its version to the repository when applicable.
- `scripts/build_and_install_dp_client.sh` — builds and installs `dp-client` (using `--no-deps`), prints diagnostics, and verifies import.

## Notes on repository layout and releases
- While dp-client is colocated here for convenience, best practice is to host it in a separate repository with its own SDLC and publish it to a package registry. Downstream projects can then depend on versioned releases.
- For now, CI and local development build `dp-client` on the fly and use the latest artifacts.
