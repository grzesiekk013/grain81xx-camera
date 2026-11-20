#!/bin/sh
SNAP_BIN="/mnt/mtd/bin/snap"
OUT_JPG="/tmp/snap.jpg"
TMP_JPG="/tmp/snap_$$_$(date +%s 2>/dev/null || echo 0).jpg"
LOCK_DIR="/tmp/snap.lock"

while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    usleep 100000 2>/dev/null || sleep 1
done
trap 'rmdir "$LOCK_DIR" 2>/dev/null; rm -f "$TMP_JPG" 2>/dev/null' EXIT INT TERM

rm -f "$TMP_JPG" 2>/dev/null
"$SNAP_BIN" 0 1280 720 "$TMP_JPG" >/dev/null 2>&1
usleep 100000 2>/dev/null || true

if [ -s "$TMP_JPG" ]; then
    rm -f "$OUT_JPG" 2>/dev/null
    mv "$TMP_JPG" "$OUT_JPG" 2>/dev/null || cp "$TMP_JPG" "$OUT_JPG"
    printf "Content-Type: image/jpeg\r\nCache-Control: no-store, no-cache, must-
revalidate\r\nPragma: no-cache\r\n\r\n"
    cat "$OUT_JPG"
else
    printf "Status: 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nN
o snapshot\n"
fi