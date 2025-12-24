#!/usr/bin/env bash
set -euo pipefail

# Usage: build-dmg.sh [project_dir] [output_dir]
PROJECT_DIR="${1:-$(cd "$(dirname "$0")"/../.. && pwd)}"
OUTPUT_DIR="${2:-${PROJECT_DIR}/dist}"

mkdir -p "$OUTPUT_DIR"

TMPDIR=$(mktemp -d /tmp/scratchattach.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Preparing files in $TMPDIR"
cp -R "$PROJECT_DIR"/* "$TMPDIR/"

# create Applications link for drag-and-drop UI in DMG
ln -s /Applications "$TMPDIR/Applications"

VOLNAME="Scratchattach"
DMG_PATH="$OUTPUT_DIR/${VOLNAME}.dmg"

echo "Creating DMG at $DMG_PATH"
hdiutil create -volname "$VOLNAME" -srcfolder "$TMPDIR" -ov -format UDZO "$DMG_PATH"

echo "DMG created: $DMG_PATH"
