#!/usr/bin/env bash
# Script de migration DB (I6)
# Applique les migrations Alembic

set -euo pipefail
cd "$(dirname "$0")/.."

echo "🔄 Migration de la base de données..."
alembic upgrade head
echo "✅ Migration terminée"
