# Authentication (JWT) — Quick Guide

Short overview of the authentication we implemented.

- Approach: JWT-only API auth using Django REST Framework + SimpleJWT.
  - Global permission is IsAuthenticated (all endpoints require a token).
  - Only exception: /api/health/ is public for probes.
  - OpenAPI via drf-spectacular advertises bearerAuth (JWT) globally.
  - Client usage relies on AuthenticatedClient with Authorization: Bearer <token>.

References
- DRF: https://www.django-rest-framework.org/
- SimpleJWT: https://django-rest-framework-simplejwt.readthedocs.io/en/latest/
- drf-spectacular: https://drf-spectacular.readthedocs.io/en/latest/

## How it works in production
- Clients obtain tokens at POST /api/token/ with JSON {"username", "password"}; response contains {"access", "refresh"}.
- Include the access token in requests: Authorization: Bearer <access>.
- Refresh short-lived access tokens at POST /api/token/refresh/ with {"refresh"}.
- Bootstrap an admin once (e.g., createsuperuser at deploy time) to manage users. Do not use DJANGO_SECRET_KEY as a token; it remains server-only for signing.

Minimal example
- Get a token:
  - curl -s -X POST "$BASE_URL/api/token/" -H 'Content-Type: application/json' -d '{"username":"<u>","password":"<p>"}'
- Call API with token:
  - curl -H "Authorization: Bearer <access>" "$BASE_URL/api/users/"

## How it works in CI/CD
- Workflow: .github/workflows/unit_tests_on_docker.yml
  - Exposes TEST_USERNAME and TEST_PASSWORD to the app container.
  - docker-compose ensures a matching Django user exists at startup (superuser by default for tests).
  - Tests obtain a JWT by calling /api/token/ and pass it with AuthenticatedClient; health probe remains unauthenticated.

## How to run manually (local)
1) Configure .env (repo root). At minimum:
   - POSTGRES_* vars, METADATA_HOST/PORT (provided), and optionally:
   - TEST_USERNAME=your_user
   - TEST_PASSWORD=your_password
2) Start stack:
   - docker compose up --build
   - The app migrates and creates/updates the test user if TEST_* vars are set.
3) Get a JWT:
   - curl -s -X POST "http://localhost:8000/api/token/" -H 'Content-Type: application/json' -d '{"username":"your_user","password":"your_password"}'
4) Call protected endpoints with Authorization: Bearer <access>.
5) Public healthcheck:
   - curl http://localhost:8000/api/health/

## Using the generated Python client
- Install the latest client you built/published, then:
  - from metadata_client import AuthenticatedClient
  - client = AuthenticatedClient(base_url=BASE_URL, token=ACCESS_TOKEN, prefix="Bearer")
- See the generated client docs or source for operation calls (users_create, users_list, etc.).

Notes
- All endpoints except /api/health/ require a valid JWT.
- Token/signing configuration is managed by SimpleJWT; adjust lifetimes/keys via settings if needed (see docs above).
