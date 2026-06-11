#!/bin/bash
set -euo pipefail

HTPASSWD_FILE="$(cd "$(dirname "$0")/../nginx" && pwd)/.htpasswd"

if command -v htpasswd &> /dev/null; then
    htpasswd -c "$HTPASSWD_FILE" admin
    echo "Done! $HTPASSWD_FILE created."
else
    echo "htpasswd not found. Install apache2-utils or run via Docker:"
    echo "  docker run --rm -it -v $(pwd)/nginx:/nginx httpd:alpine htpasswd -c /nginx/.htpasswd admin"
    exit 1
fi
