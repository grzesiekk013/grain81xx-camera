#!/bin/sh
BIN="/mnt/mtd/bin/snap_faster"
PID_FILE="/tmp/stream.pid"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        kill "$OLD_PID" 2>/dev/null
        usleep 200000 2>/dev/null || sleep 1
    fi
fi

echo $$ > "$PID_FILE"
exec "$BIN" 0 1280 720 mjpeg 0 25 0