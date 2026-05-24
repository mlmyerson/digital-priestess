#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"
PIDS=()

env_file_value() {
    local key="$1"
    local line=""
    if [[ -f "$ROOT/.env" ]]; then
        line="$(grep -E "^[[:space:]]*${key}=" "$ROOT/.env" | tail -n 1 || true)"
    fi
    if [[ -z "$line" ]]; then
        return 1
    fi
    local value="${line#*=}"
    value="${value%$'\r'}"
    value="${value%\"}"
    value="${value#\"}"
    printf '%s' "$value"
}

load_env_value() {
    local key="$1"
    local value=""
    if [[ -n "${!key:-}" ]]; then
        return 0
    fi
    if value="$(env_file_value "$key")"; then
        export "$key=$value"
    fi
}

repo_path_from_windows_path() {
    local value="$1"
    local normalized="${value//\\//}"
    if [[ "$normalized" == *"/digital-priestess/"* ]]; then
        printf '%s/%s' "$ROOT" "${normalized#*'/digital-priestess/'}"
    else
        printf '%s' "$value"
    fi
}

for key in APP_HOST APP_PORT LM_STUDIO_BASE_URL LM_STUDIO_MODEL LM_STUDIO_TIMEOUT_SECONDS ARCHIVE_ROOT DATA_DIR ALLOWED_ORIGINS; do
    load_env_value "$key"
done

export APP_HOST="${APP_HOST:-0.0.0.0}"
export APP_PORT="${APP_PORT:-8787}"
export LM_STUDIO_BASE_URL="${LM_STUDIO_BASE_URL:-http://host.docker.internal:1234/v1}"
export LM_STUDIO_MODEL="${LM_STUDIO_MODEL:-local-model}"
export ARCHIVE_ROOT="${ARCHIVE_ROOT:-$ROOT/docs/Writing}"
export DATA_DIR="${DATA_DIR:-$ROOT/.local/data}"
export VITE_BACKEND_URL="${VITE_BACKEND_URL:-http://127.0.0.1:${APP_PORT}}"
export VITE_HOST="${VITE_HOST:-0.0.0.0}"
export VITE_PORT="${VITE_PORT:-5173}"

if [[ -f /.dockerenv && "$APP_HOST" == "127.0.0.1" ]]; then
    export APP_HOST="0.0.0.0"
fi

if [[ -f /.dockerenv && ("$LM_STUDIO_BASE_URL" == "http://127.0.0.1:1234/v1" || "$LM_STUDIO_BASE_URL" == "http://localhost:1234/v1") ]]; then
    export LM_STUDIO_BASE_URL="http://host.docker.internal:1234/v1"
fi

if [[ "$ARCHIVE_ROOT" == *\\* ]]; then
    export ARCHIVE_ROOT="$(repo_path_from_windows_path "$ARCHIVE_ROOT")"
fi

if [[ "$DATA_DIR" == *\\* ]]; then
    export DATA_DIR="$(repo_path_from_windows_path "$DATA_DIR")"
fi

if [[ "$ARCHIVE_ROOT" != /* ]]; then
    export ARCHIVE_ROOT="$ROOT/$ARCHIVE_ROOT"
fi

if [[ "$DATA_DIR" != /* ]]; then
    export DATA_DIR="$ROOT/$DATA_DIR"
fi

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait "${PIDS[@]}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

mkdir -p "$DATA_DIR"

if [[ ! -x "$BACKEND_PYTHON" ]]; then
    python3 -m venv "$BACKEND_DIR/.venv"
fi

if ! "$BACKEND_PYTHON" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
    "$BACKEND_PYTHON" -m pip install -e "$BACKEND_DIR[dev,ingest]"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    npm --prefix "$FRONTEND_DIR" install
fi

echo "Starting backend..."
(cd "$BACKEND_DIR" && exec "$BACKEND_PYTHON" -m uvicorn app.main:app --host "$APP_HOST" --port "$APP_PORT" --reload) &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

echo "Starting frontend..."
(cd "$FRONTEND_DIR" && exec npm run dev) &
FRONTEND_PID=$!
PIDS+=("$FRONTEND_PID")

echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "Backend: http://127.0.0.1:$APP_PORT"
echo "Frontend: Vite will print the active URL, starting with port $VITE_PORT."
echo "Archive root: $ARCHIVE_ROOT"
echo "Data dir: $DATA_DIR"
echo "LM Studio: $LM_STUDIO_BASE_URL ($LM_STUDIO_MODEL)"
echo "Press Ctrl+C to stop."
wait -n "${PIDS[@]}"
