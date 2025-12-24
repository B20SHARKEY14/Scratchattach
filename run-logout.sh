#!/usr/bin/env bash
# Logout helper — removes saved session and clears SCRATCH_SESSION_STRING from .env
set -euo pipefail

# Resolve script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/.env"
SESSION_FILE="$HOME/.scratchattach_session"

echo "Removing saved session file: $SESSION_FILE"
rm -f "$SESSION_FILE" || true

if [ -f "$ENV_FILE" ]; then
	echo "Removing SCRATCH_SESSION_STRING from $ENV_FILE"
	sed -E '/^SCRATCH_SESSION_STRING=/d' "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
	echo "Updated $ENV_FILE"
else
	echo "No .env file at $ENV_FILE"
fi

echo "Logout complete."
