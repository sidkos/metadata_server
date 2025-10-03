#!/bin/bash
CLIENT_DIR="metadata-client"
CLIENT_NAME="metadata_client"

./scripts/build_open_api_client.sh

echo "Installing Metadata client package locally"
VERSION=$(grep "__version__" setup.py | awk -F '"' '{print $2}')
pip install ./$CLIENT_DIR/dist/$CLIENT_NAME-"$VERSION"-py3-none-any.whl --force-reinstall || exit 1
echo "OpenAPI client installed locally"

rm -rf $CLIENT_DIR
