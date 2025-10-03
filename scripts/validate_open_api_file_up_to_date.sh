#!/bin/bash

FAIL_ON_ERROR=false


while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --fail)
            FAIL_ON_ERROR=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

source ./.venv/bin/activate

echo "Generate OpenAPI specification..."
python src/manage.py spectacular --file src/open_api_spec.yml


if ! git diff --exit-code --quiet src/open_api_spec.yml; then
    echo "OpenAPI specification has changed. Please commit also the change!"
    if $FAIL_ON_ERROR; then
        exit 1
    fi
fi
