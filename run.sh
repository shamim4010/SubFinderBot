#!/usr/bin/env bash
# Bot bondho hole nije nije abar chalu hoy (crash-proof loop)
cd "$(dirname "$0")"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
while true; do
  echo "[$(date '+%H:%M:%S')] SubFinder 2050 chalu hocche..."
  python3 bot.py
  echo "Bot theme gelo, 5 second por abar chalu hobe (Ctrl+C dile bondho)"
  sleep 5
done
