#!/usr/bin/env bash
# Symlink this skill into ~/.cola/skills so SkillWatcher picks it up.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.cola/skills/knowledge-motion-video"
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  echo "already installed at $DEST"
  exit 0
fi
ln -s "$SRC" "$DEST"
echo "installed: $DEST -> $SRC"
