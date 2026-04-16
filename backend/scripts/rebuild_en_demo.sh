#!/usr/bin/env bash
# Полный пересев EN-демо в локальный SQLite и проверка графа.
# Использование: из каталога backend/:  bash scripts/rebuild_en_demo.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d .venv ]]; then
  echo "Create backend/.venv first (python -m venv .venv && pip install -r requirements.txt)"
  exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate
export SEED_USE_SQLITE="${SEED_USE_SQLITE:-1}"
export SEED_SQLITE_URL="${SEED_SQLITE_URL:-sqlite:///./memorial.db}"
rm -f memorial.db
python seed_english_all.py
python verify_en_demo_graph.py
echo "Optional portraits (network, same SQLite as above):"
echo "  SEED_USE_SQLITE=1 python clear_en_demo_covers.py && SEED_USE_SQLITE=1 python seed_english_portraits.py"
