#!/usr/bin/env bash
# Run Cline (headless) against the gwarden.su gateway.
# Same agent as app.cline.bot, but with a custom OpenAI-compatible provider.
set -euo pipefail

: "${GWARDEN_API_KEY:?GWARDEN_API_KEY is required}"
CLINE_BASE_URL="${CLINE_BASE_URL:-https://gwarden.su/v1}"
CLINE_MODEL="${CLINE_MODEL:-gemini-4-argon}"
CLINE_TASK="${CLINE_TASK:?CLINE_TASK is required}"
CLINE_TIMEOUT="${CLINE_TIMEOUT:-1800}"
CLINE_AUTO_APPROVE="${CLINE_AUTO_APPROVE:-true}"
CLINE_CWD="${CLINE_CWD:-/workspace}"

auth_args=(-p openai-compatible -k "$GWARDEN_API_KEY" -m "$CLINE_MODEL" -b "$CLINE_BASE_URL")
run_args=(--json --auto-approve "$CLINE_AUTO_APPROVE" -t "$CLINE_TIMEOUT")

if [[ -n "${CLINE_CONFIG:-}" ]]; then
  auth_args+=(--config "$CLINE_CONFIG")
  run_args+=(--config "$CLINE_CONFIG")
fi
if [[ -n "${CLINE_DATA_DIR:-}" ]]; then
  auth_args+=(--data-dir "$CLINE_DATA_DIR")
  run_args+=(--data-dir "$CLINE_DATA_DIR")
fi

echo "[cline-cloud] provider=openai-compatible base=${CLINE_BASE_URL} model=${CLINE_MODEL} cwd=${CLINE_CWD}" >&2
cline auth "${auth_args[@]}" >&2

cd "$CLINE_CWD"
exec cline "${run_args[@]}" "$CLINE_TASK"
