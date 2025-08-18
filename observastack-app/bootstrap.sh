#!/usr/bin/env bash
set -euo pipefail
REPO_URL="${1:-}"
if [[ -z "$REPO_URL" ]]; then
  echo "Usage: ./bootstrap.sh <git-remote-url>"; exit 1; fi
git init -b master
git add .
git commit -m "chore: initial scaffold (observastack-app)"
git remote add origin "$REPO_URL"
git push -u origin master
