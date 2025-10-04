# dp-client

A unified, test-friendly client to interact with the platform during component/integration tests.

- Lives in its own folder (dp-client)
- Built and versioned similarly to metadata-client
- Depends on the generated `metadata-client`
- Has its own requirements file (requirements.txt)

## Installation (development)

Option A: Install from requirements

```bash
pip install -r dp-client/requirements.txt
```

Option B: Build with Poetry and install the wheel

```bash
./scripts/build_dp_client.sh
pip install ./dp-client/dist/*.whl
```

## Usage

```python
from dp_client import DPClient

client = DPClient(base_url="http://localhost:8000")

# Backward-compatible helpers:
client.health_check()
client.create_user({"id": "...", "name": "...", "phone": "+972...", "address": "..."})
client.get_user("...")
client.list_users()

# Structured access:
# Underlying generated client (metadata-client):
client.MetaDataServerAPIClient

# API domains:
client.HealthAPI.health_check()
client.UsersApi.create_user({...})

# Optional DB helper (uses Django ORM if available in the environment):
client.PGDBClient.get_user_by_id("...")
client.PGDBClient.delete_users_by_ids(["...", "..."])
```


## Running DB-backed component tests locally

You have two options to make DB checks work outside Docker:

1) Use docker-compose (recommended):
   - Ensure the Postgres service is up and reachable as host name `db` within the network.
   - From repo root: `docker-compose up -d`
   - Run tests; the `.env` sets POSTGRES_HOST=db and tests will connect via that.

2) Use a local Postgres instance:
   - Export env vars to point at your local instance, for example:
     - `export POSTGRES_HOST=localhost`
     - `export POSTGRES_PORT=5432`
     - `export POSTGRES_DB=postgres`
     - `export POSTGRES_USER=postgres`
     - `export POSTGRES_PASSWORD=postgres`
   - Or, if your `.env` uses POSTGRES_HOST=db and you don’t want to change it, you can opt-in to a safe fallback:
     - `export POSTGRES_ALLOW_LOCAL_FALLBACK=true`
     - When the host `db` is not resolvable, dp-client will transparently fall back to `localhost`.

If the DB is not reachable, component tests that require direct DB access will be skipped with a helpful message.
