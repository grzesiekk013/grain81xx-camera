#!/bin/sh
printf "Content-Type: textplain; charset=utf-8\r\nCache-Control: no-store\r\n\r\n"

PTZ_BIN="/mnt/mtd/bin/ptz_test"
POS_FILE="/tmp/ptz_pos"
LOCK_DIR="/tmp/ptz.lock"

[ -f "$POS_FILE" ] || printf "0 0\n" > "$POS_FILE"

while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    usleep 5000 2>/dev/null || sleep 1
done
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT INT TERM

QS="$QUERY_STRING"
get_param() {
    printf "%s" "$QS" | tr '&' '\n' | sed -n "s/^$1=//p" | head -n 1 | tr -cd '0-9a-zA-Z_-'
}

CMD=$(get_param cmd)
DIR=$(get_param dir)
STEPS=$(get_param steps)
VAL=$(get_param val)
TX=$(get_param x)
TY=$(get_param y)

read CUR_X CUR_Y < "$POS_FILE"
CUR_X=${CUR_X:-0}
CUR_Y=${CUR_Y:-0}

case "$CMD" in
    pan)
        DIR=${DIR:-0}
        STEPS=${STEPS:-10}
        [ "$STEPS" -gt 0 ] && "$PTZ_BIN" pan "$DIR" "$STEPS"
        if [ "$DIR" = "0" ]; then
            CUR_X=$((CUR_X - STEPS))
        else
            CUR_X=$((CUR_X + STEPS))
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK pan dir=%s steps=%s pos=%d,%d\n" "$DIR" "$STEPS" "$CUR_X" "$CUR_Y"
        ;;
    tilt)
        DIR=${DIR:-0}
        STEPS=${STEPS:-10}
        [ "$STEPS" -gt 0 ] && "$PTZ_BIN" tilt "$DIR" "$STEPS"
        if [ "$DIR" = "0" ]; then
            CUR_Y=$((CUR_Y - STEPS))
        else
            CUR_Y=$((CUR_Y + STEPS))
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK tilt dir=%s steps=%s pos=%d,%d\n" "$DIR" "$STEPS" "$CUR_X" "$CUR_Y"
        ;;
    goto)
        TX=${TX:-$CUR_X}
        TY=${TY:-$CUR_Y}
        DX=$((TX - CUR_X))
        DY=$((TY - CUR_Y))
        if [ "$DX" -lt 0 ]; then
            ABS_DX=$((-DX))
            "$PTZ_BIN" pan 0 "$ABS_DX"
            CUR_X=$((CUR_X - ABS_DX))
        elif [ "$DX" -gt 0 ]; then
            "$PTZ_BIN" pan 1 "$DX"
            CUR_X=$((CUR_X + DX))
        fi
        if [ "$DY" -lt 0 ]; then
            ABS_DY=$((-DY))
            "$PTZ_BIN" tilt 0 "$ABS_DY"
            CUR_Y=$((CUR_Y - ABS_DY))
        elif [ "$DY" -gt 0 ]; then
            "$PTZ_BIN" tilt 1 "$DY"
            CUR_Y=$((CUR_Y + DY))
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK goto target=%s,%s pos=%d,%d\n" "$TX" "$TY" "$CUR_X" "$CUR_Y"
        ;;
    ircut)
        VAL=${VAL:-0}
        "$PTZ_BIN" ircut "$VAL"
        printf "OK ircut=%s\n" "$VAL"
        ;;
    irled)
        VAL=${VAL:-0}
        "$PTZ_BIN" irled "$VAL"
        printf "OK irled=%s\n" "$VAL"
        ;;
    *)
        printf "ERR unknown cmd\n"
        exit 1
        ;;
esac
