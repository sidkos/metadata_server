#!/usr/bin/env bash
set -euo pipefail

# This script runs inside the app container. It expects the following env vars:
# - DJANGO_* for Django config
# - POSTGRES_* for DB connectivity
# - TEST_USERNAME / TEST_PASSWORD (optional) to ensure a test superuser exists

cd /app

echo "[container] Running migrations..."
python src/manage.py migrate --noinput

if [[ -n "${TEST_USERNAME:-}" && -n "${TEST_PASSWORD:-}" ]]; then
  echo "[container] Ensuring test user ${TEST_USERNAME} exists..."
  python - <<'PY'
import os
# Ensure Django is configured for standalone script execution
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
U = get_user_model()
u = os.environ.get('TEST_USERNAME')
p = os.environ.get('TEST_PASSWORD')
user, created = U.objects.get_or_create(username=u, defaults={'is_staff': True, 'is_superuser': True})
user.set_password(p)
user.save()
print('Test user ensured:', user.username)
PY
else
  echo "[container] TEST_USERNAME/TEST_PASSWORD not set; skipping test user creation"
fi

echo "[container] Starting Django server..."
exec python src/manage.py runserver 0.0.0.0:8000
