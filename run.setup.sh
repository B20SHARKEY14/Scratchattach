make setup-env
# or
make run-setup#!/usr/bin/env bash
# Interactive .env setup — prompts for common SCRATCH_* variables
set -euo pipefail

# Resolve script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/.env"
EXAMPLE_FILE="$DIR/.env.example"

# Keys we support editing
KEYS=(
"SCRATCH_SESSION_STRING"
"SCRATCH_LOGIN_USERNAME"
"SCRATCH_LOGIN_PASSWORD"
"SCRATCH_USERNAME"
)

echo "Environment setup — writing to $ENV_FILE"

# Read current value for a key from .env (do not source arbitrary files)
get_current() {
	local key="$1"
	if [ -f "$ENV_FILE" ]; then
		local line
		line=$(grep -m1 -E "^${key}=" "$ENV_FILE" || true)
		if [ -n "$line" ]; then
			# strip key and optional quotes
			printf "%s" "${line#${key}=}" | sed -E 's/^"(.*)"$/\1/'
			return
		fi
	fi
	# fallback to environment
	printf "%s" "${!key:-}"
}

# If .env.example exists, read defaults from it
read_example() {
	local key="$1"
	if [ -f "$EXAMPLE_FILE" ]; then
		local line
		line=$(grep -m1 -E "^${key}=" "$EXAMPLE_FILE" || true)
		if [ -n "$line" ]; then
			printf "%s" "${line#${key}=}" | sed -E 's/^"(.*)"$/\1/'
			return
		fi
	fi
	printf ""
}

NEW_LINES=()

# Non-interactive if stdin is not a TTY or SKIP_PROMPTS=1 is set
NONINTERACTIVE=0
if [ ! -t 0 ] || [ "${SKIP_PROMPTS-0}" = "1" ]; then
	NONINTERACTIVE=1
fi

for key in "${KEYS[@]}"; do
	# Priority: existing .env -> environment var -> .env.example -> empty
	cur=$(get_current "$key")
	if [ -z "$cur" ]; then
		cur="$(read_example "$key")"
	fi

	# If an environment variable explicitly provided, use it without prompting
	if [ -n "${!key-}" ]; then
		val="${!key}"
	elif [ "$NONINTERACTIVE" -eq 1 ]; then
		# non-interactive: accept current or example value
		val="$cur"
	else
		if [ -n "$cur" ]; then
			prompt="[$cur]"
		else
			prompt="[empty]"
		fi
		read -rp "Value for ${key} ${prompt}: " val || true
		if [ -z "$val" ]; then
			val="$cur"
		fi
	fi

	# Only write keys that have a non-empty value
	if [ -n "$val" ]; then
		# escape backslashes and double quotes
		esc=$(printf "%s" "$val" | sed 's/\\/\\\\/g; s/"/\\"/g')
		NEW_LINES+=("${key}=\"${esc}\"")
	fi
done

# Preserve other lines from existing .env that do not match our keys
tmpfile=$(mktemp)
if [ -f "$ENV_FILE" ]; then
	# remove lines for our keys
	grep -v -E '^('"$(IFS='|'; echo "${KEYS[*]}")"')=' "$ENV_FILE" > "$tmpfile" || true
fi

for l in "${NEW_LINES[@]}"; do
	echo "$l" >> "$tmpfile"
done

mv "$tmpfile" "$ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true
echo "Wrote $ENV_FILE"
