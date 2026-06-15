#!/usr/bin/env bash
# Shortcut to open the GitHub CI test container.
set -euo pipefail
cd "$(dirname "$0")"
docker compose -f ci-test.yml run --rm github-ci-test "$@"
