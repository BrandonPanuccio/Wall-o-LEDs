#!/usr/bin/env bash
# run.sh — start lyrics mode

# exit immediately if something fails
set -e

# cd to the script's folder (so it works from anywhere)
cd "$(dirname "$0")"

# activate venv
if [ ! -d ".venv" ]; then
  echo "❌ No .venv found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source .venv/bin/activate

# run the program
python3 main.py
