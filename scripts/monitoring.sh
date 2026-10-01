#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
if (( EUID == 0 )); then
    exec docker compose -f compose.yaml -f compose.monitoring.yaml "$@"
fi
exec sudo docker compose -f compose.yaml -f compose.monitoring.yaml "$@"
