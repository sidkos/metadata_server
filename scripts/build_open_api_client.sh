#!/bin/bash

CLIENT_DIR="metadata-client"
CLIENT_CONFIG="metadata_client.yaml"

if ! swagger-cli --version > /dev/null 2>&1; then
    echo "Installing swagger-cli"
    npm install -g swagger-cli
fi

echo "Validating OpenAPI Spec"
if ! swagger-cli validate "./src/open_api_spec.yml"; then
    echo "OpenAPI document validation failed."
    exit 1
fi

rm -rf $CLIENT_DIR

echo "Installing build dependencies"
pip install -r requirements-build-client.txt

echo "Generating OpenAPI client"
openapi-python-client generate --meta poetry --path ./src/open_api_spec.yml --config $CLIENT_CONFIG

version=$(grep "__version__" setup.py | awk -F '"' '{print $2}')

cd $CLIENT_DIR

# Pin attrs to a compatible range for the generated client
sed -e 's/^attrs .*$/attrs = ">=21.3.0,<24.0.0"/' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml

# Scope the package name for GitHub Packages PyPI as <owner>/<package>
if [ -n "${REPOSITORY_OWNER:-}" ]; then
  echo "Scoping package name to ${REPOSITORY_OWNER}/metadata-client for GitHub Packages"
  sed -E 's/^name\s*=\s*"[^"]+"/name = "'"${REPOSITORY_OWNER}"'\/metadata-client"/' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
else
  echo "REPOSITORY_OWNER is not set; leaving package name unchanged (this may break GitHub Packages upload)"
fi

poetry version $version

echo "Building the OpenAPI client package with Poetry"
poetry build

echo "OpenAPI client package built successfully"

