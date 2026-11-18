#!/bin/bash
# Install or update the pfstack skill for Claude Code (and Codex if present).
#   bash install.sh            from a clone
# Clones/pulls chux0519/pfstack into $PFSTACK_HOME (default ~/repos/pfstack) when run elsewhere,
# then links skill/pfstack into ~/.claude/skills (and ~/.codex/skills if that folder exists).
# Idempotent; never deletes anything but its own symlink.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
if [ -d "$HERE/skill/pfstack" ]; then
  HOME_DIR=$HERE
else
  HOME_DIR=${PFSTACK_HOME:-$HOME/repos/pfstack}
  if [ -d "$HOME_DIR/.git" ]; then git -C "$HOME_DIR" pull -q --ff-only
  else git clone -q https://github.com/chux0519/pfstack "$HOME_DIR"; fi
fi
[ -d "$HERE/.git" ] && [ "$HOME_DIR" = "$HERE" ] && git -C "$HOME_DIR" pull -q --ff-only || true
for dir in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  [ "$dir" = "$HOME/.codex/skills" ] && [ ! -d "$HOME/.codex" ] && continue
  mkdir -p "$dir"
  if [ -e "$dir/pfstack" ] && [ ! -L "$dir/pfstack" ]; then
    echo "skip $dir/pfstack: exists and is not a symlink (move it away first)"; continue
  fi
  ln -sfn "$HOME_DIR/skill/pfstack" "$dir/pfstack"
  echo "linked $dir/pfstack -> $HOME_DIR/skill/pfstack"
done
python3 "$HOME_DIR/skill/pfstack/scripts/pfstack.py" --help >/dev/null && echo "pfstack ready: in any project say /pfstack"
