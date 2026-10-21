#!/usr/bin/env bash
set -euo pipefail
exec python3 /usr/local/share/tripwire/native_route_trace.py "$@"
