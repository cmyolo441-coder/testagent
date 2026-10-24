#!/usr/bin/env bash
# List the model IDs the gateway exposes, so you can pick one for
# CLINE_MODEL / `-f model=...`.
#   GWARDEN_API_KEY=... bash cloud/list-models.sh
set -euo pipefail

: "${GWARDEN_API_KEY:?GWARDEN_API_KEY is required}"
base="${CLINE_BASE_URL:-https://gwarden.su/v1}"

curl -sS "$base/models" -H "Authorization: Bearer $GWARDEN_API_KEY" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);j.data.forEach(m=>console.log(m.id))})'
