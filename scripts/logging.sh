#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
args=(-f compose.yaml -f compose.monitoring.yaml -f compose.logging.yaml)
if (( EUID == 0 )); then
    exec docker compose "${args[@]}" "$@"
fi
exec sudo docker compose "${args[@]}" "$@"
