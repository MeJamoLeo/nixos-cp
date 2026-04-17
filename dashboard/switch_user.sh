#!/usr/bin/env bash
# Switch dashboard to next user or specific user
# Usage: switch_user.sh [username|next]
CACHE_DIR="$HOME/.cache/cp-dashboard"
mkdir -p "$CACHE_DIR"
USER="${1:-next}"
if [[ ! "$USER" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "Error: invalid username" >&2
    exit 1
fi
echo "$USER" > "$CACHE_DIR/switch_user"
