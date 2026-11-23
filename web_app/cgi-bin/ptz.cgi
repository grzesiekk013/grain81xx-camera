#!/bin/sh
printf "Content-Type: text/plain; charset=utf-8\r\nCache-Control: no-store\r\n\r\n"

PTZ_BIN="/mnt/mtd/bin/ptz_test"
POS_FILE="/tmp/ptz_pos"
LOCK_DIR="/tmp/ptz.lock"

MAX_X=625
MAX_Y=140
CENTER_X=312
CENTER_Y=70

while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    usleep 5000 2>/dev/null || sleep 1
done
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT INT TERM

QS="$QUERY_STRING"
get_param() {
    printf "%s" "$QS" | tr '&' '\n' | sed -n "s/^$1=//p" | head -n 1 | tr -cd '0-9a-zA-Z_-'
}

clamp() {
    val="$1"
    min_v="$2"
    max_v="$3"
    [ "$val" -lt "$min_v" ] && val="$min_v"
    [ "$val" -gt "$max_v" ] && val="$max_v"
    printf "%d" "$val"
}

run_move() {
    axis="$1"
    dir="$2"
    steps="$3"
    [ "$steps" -gt 0 ] || { printf "OK\n"; return 0; }
    out=$("$PTZ_BIN" "$axis" "$dir" "$steps" 2>&1)
    rc=$?
    printf "%s\n" "$out"
    return "$rc"
}

CMD=$(get_param cmd)
DIR=$(get_param dir)
STEPS=$(get_param steps)
VAL=$(get_param val)
TX=$(get_param x)
TY=$(get_param y)
CENTER=$(get_param center)

do_home() {
    out_x=$(run_move pan 0 $((MAX_X + 50)))
    out_y=$(run_move tilt 0 $((MAX_Y + 30)))
    CUR_X=0
    CUR_Y=0
    if [ "$CENTER" = "1" ]; then
        run_move pan 1 "$CENTER_X" >/dev/null
        run_move tilt 1 "$CENTER_Y" >/dev/null
        CUR_X="$CENTER_X"
        CUR_Y="$CENTER_Y"
    fi
    printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
    printf "OK home pos=%d,%d\n" "$CUR_X" "$CUR_Y"
}

if [ ! -f "$POS_FILE" ] && [ "$CMD" != "home" ]; then
    do_home
    exit 0
fi

read CUR_X CUR_Y < "$POS_FILE" 2>/dev/null
CUR_X=$(clamp "${CUR_X:-0}" 0 "$MAX_X")
CUR_Y=$(clamp "${CUR_Y:-0}" 0 "$MAX_Y")

case "$CMD" in
    home)
        do_home
        ;;
    pan)
        DIR=${DIR:-0}
        STEPS=${STEPS:-10}
        if [ "$STEPS" -gt 0 ]; then
            if [ "$DIR" = "0" ]; then
                target=$(clamp $((CUR_X - STEPS)) 0 "$MAX_X")
                actual=$((CUR_X - target))
                res=$(run_move pan 0 "$actual")
                case "$res" in
                    *"Limit: LEFT"*) CUR_X=0 ;;
                    *) CUR_X="$target" ;;
                esac
            else
                target=$(clamp $((CUR_X + STEPS)) 0 "$MAX_X")
                actual=$((target - CUR_X))
                res=$(run_move pan 1 "$actual")
                case "$res" in
                    *"Limit: RIGHT"*) CUR_X="$MAX_X" ;;
                    *) CUR_X="$target" ;;
                esac
            fi
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK pan dir=%s steps=%s pos=%d,%d\n" "$DIR" "$STEPS" "$CUR_X" "$CUR_Y"
        ;;
    tilt)
        DIR=${DIR:-0}
        STEPS=${STEPS:-10}
        if [ "$STEPS" -gt 0 ]; then
            if [ "$DIR" = "0" ]; then
                target=$(clamp $((CUR_Y - STEPS)) 0 "$MAX_Y")
                actual=$((CUR_Y - target))
                res=$(run_move tilt 0 "$actual")
                case "$res" in
                    *"Limit: DOWN"*) CUR_Y=0 ;;
                    *) CUR_Y="$target" ;;
                esac
            else
                target=$(clamp $((CUR_Y + STEPS)) 0 "$MAX_Y")
                actual=$((target - CUR_Y))
                res=$(run_move tilt 1 "$actual")
                case "$res" in
                    *"Limit: UP"*) CUR_Y="$MAX_Y" ;;
                    *) CUR_Y="$target" ;;
                esac
            fi
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK tilt dir=%s steps=%s pos=%d,%d\n" "$DIR" "$STEPS" "$CUR_X" "$CUR_Y"
        ;;
    goto)
        TX=$(clamp "${TX:-$CUR_X}" 0 "$MAX_X")
        TY=$(clamp "${TY:-$CUR_Y}" 0 "$MAX_Y")
        DX=$((TX - CUR_X))
        DY=$((TY - CUR_Y))
        if [ "$DX" -lt 0 ]; then
            res=$(run_move pan 0 $((-DX)))
            case "$res" in
                *"Limit: LEFT"*) CUR_X=0 ;;
                *) CUR_X="$TX" ;;
            esac
        elif [ "$DX" -gt 0 ]; then
            res=$(run_move pan 1 "$DX")
            case "$res" in
                *"Limit: RIGHT"*) CUR_X="$MAX_X" ;;
                *) CUR_X="$TX" ;;
            esac
        fi
        if [ "$DY" -lt 0 ]; then
            res=$(run_move tilt 0 $((-DY)))
            case "$res" in
                *"Limit: DOWN"*) CUR_Y=0 ;;
                *) CUR_Y="$TY" ;;
            esac
        elif [ "$DY" -gt 0 ]; then
            res=$(run_move tilt 1 "$DY")
            case "$res" in
                *"Limit: UP"*) CUR_Y="$MAX_Y" ;;
                *) CUR_Y="$TY" ;;
            esac
        fi
        printf "%d %d\n" "$CUR_X" "$CUR_Y" > "$POS_FILE"
        printf "OK goto target=%d,%d pos=%d,%d\n" "$TX" "$TY" "$CUR_X" "$CUR_Y"
        ;;
    ircut)
        VAL=${VAL:-0}
        "$PTZ_BIN" ircut "$VAL" >/dev/null 2>&1
        printf "OK ircut=%s\n" "$VAL"
        ;;
    irled)
        VAL=${VAL:-0}
        "$PTZ_BIN" irled "$VAL" >/dev/null 2>&1
        printf "OK irled=%s\n" "$VAL"
        ;;
    *)
        printf "ERR unknown cmd\n"
        exit 1
        ;;
esac