#!/bin/bash

SPEC_FILE="src/open_api_spec.yml"

HASH_FILE="src/api_spec_hash.md5"

current_hash() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        md5 -q "$SPEC_FILE"
    else
        md5sum "$SPEC_FILE" | awk '{print $1}'
    fi
}

if [ ! -f "$SPEC_FILE" ]; then
    echo "The OpenAPI spec file does not exist. Please generate it first."
    exit 1
fi

need_to_build_client=false

if [ -f "$HASH_FILE" ]; then
    saved_hash=$(cat "$HASH_FILE")
    if [ "$(current_hash)" != "$saved_hash" ]; then
        echo "The API spec has changed."
        need_to_build_client=true
    fi
else
    echo "Hash file does not exist. Should build the client."
    need_to_build_client=true
fi

if [ "$need_to_build_client" != true ]; then
    echo "Client is up to date. No need to build."
    exit 0
fi

echo "Building and install the client"
./scripts/build_and_install_open_api_client.sh || exit 1
echo "$(current_hash)" > "$HASH_FILE"
