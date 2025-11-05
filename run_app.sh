#!/usr/bin/env bash
# Script de lancement Banking Simulator (Unix)
# Version: 0.5.0

set -euo pipefail
cd "$(dirname "$0")"
streamlit run app/main.py --server.headless false

