#!/usr/bin/env bash
# Switch dashboard to next user or specific user
# Usage: switch_user.sh [username|next]
CACHE_DIR="$HOME/.cache/cp-dashboard"
mkdir -p "$CACHE_DIR"
echo "${1:-next}" > "$CACHE_DIR/switch_user"
