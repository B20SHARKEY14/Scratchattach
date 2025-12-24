#!/usr/bin/env bash
# Launcher for main.py — loads .env, sets PYTHONPATH, runs the script
set -euo pipefail

# Resolve script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/.env"
LOCAL_PKGS="$DIR/.local-packages"

# Allow overriding Python executable via env var `PYTHON`
PYTHON="${PYTHON:-/usr/bin/python3}"

# Load .env file if present (exports variables)
if [ -f "$ENV_FILE" ]; then
	# shellcheck disable=SC1090
	set -a
	# shellcheck source=/dev/null
	source "$ENV_FILE"
	set +a
fi

# Ensure .local-packages is added to PYTHONPATH when present
if [ -d "$LOCAL_PKGS" ]; then
	if [ -z "${PYTHONPATH-}" ]; then
		export PYTHONPATH="$LOCAL_PKGS"
	else
		export PYTHONPATH="$LOCAL_PKGS:$PYTHONPATH"
	fi
else
	echo "Warning: local packages directory not found: $LOCAL_PKGS"
	echo "You can install required packages locally with:" \
			 "/usr/bin/python3 -m pip install --target=.local-packages scratchattach"
fi

# If user just wants help, show short usage
if [ "$#" -eq 0 ]; then
	echo "Usage: $0 [main.py args]"
	echo "Examples:" 
	echo "  $0 griffpatch                         # fetch public user data"
	echo "  $0 griffpatch --browser-login          # authenticate via browser"
	echo "  PYTHON=/usr/bin/python3 $0 griffpatch  # use a different python"
	echo
fi

exec "$PYTHON" "$DIR/main.py" "$@"
