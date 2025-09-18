#!/usr/bin/env bash
# stop.sh — stop the lyrics mode

# exit if any command fails
set -e

# Find processes running main.py in this folder
PIDS=$(ps aux | grep "[p]ython3 main.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
  echo "⚠️  No running lyrics process found."
  exit 0
fi

echo "🔴 Stopping lyrics process(es): $PIDS"
kill $PIDS
