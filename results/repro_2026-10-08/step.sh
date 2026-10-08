#!/usr/bin/env bash
# usage: step.sh NAME CMD...   run from clone root, logs rc and wall time
O=/tmp/claude-0/-home-claude/339fffb6-0a3b-567c-954d-81548aaad86f/scratchpad/out
name="$1"; shift
s=$(date +%s.%N)
timeout 575 "$@" > "$O/stdout/$name.txt" 2>&1
rc=$?
e=$(date +%s.%N)
w=$(python3 -c "print(f'{$e-$s:.1f}')")
printf '%s\t%s\t%s\t%s\n' "$name" "$rc" "$w" "$*" >> "$O/steps.tsv"
echo "$name rc=$rc wall=${w}s"; tail -3 "$O/stdout/$name.txt"
