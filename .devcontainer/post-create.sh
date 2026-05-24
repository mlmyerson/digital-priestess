#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

sudo mkdir -p backend/.venv frontend/node_modules .local/data /home/vscode/.npm /home/vscode/.cache/pip
sudo chown -R "$(id -u):$(id -g)" backend/.venv frontend/node_modules .local /home/vscode/.npm /home/vscode/.cache

python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -e "./backend[dev,ingest]"

npm --prefix frontend install

cat <<'INFO'

Digital Priestess devcontainer is ready.

Run the full app:
  ./run.sh

The repo is bind-mounted at /workspaces/digital-priestess.
Repo-local dependency/data directories use named Docker volumes:
  backend/.venv, frontend/node_modules, .local

LM Studio should be reachable from the container at:
  http://host.docker.internal:1234/v1

INFO