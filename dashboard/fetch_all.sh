#!/usr/bin/env bash
# Fetch stats for all users in watchlist
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCHLIST="$SCRIPT_DIR/watchlist.json"

if [[ ! -f "$WATCHLIST" ]]; then
    echo "Error: watchlist.json not found" >&2
    exit 1
fi

python3 -c "
import json, subprocess, sys, os
watchlist = json.load(open('$WATCHLIST'))
script = os.path.join('$SCRIPT_DIR', 'fetch_stats.py')
for user in watchlist:
    print(f'Fetching {user}...', file=sys.stderr)
    out = os.path.expanduser(f'~/.cache/cp-dashboard/stats_{user}.json')
    subprocess.run(['python3', script, '--user', user, '--output', out])
"
