#!/bin/bash
cd /home/claude/sgc-zx
export AQORA_TEAM_ORG=learned_zx_rewriting
for f in vbe_adder_3 hwb6 grover_5; do
  python3 submit/run_emulator.py --platform nexus:H2-2E --family B1 --pipelines P0,P2 --shots 1000 --noisy true --select "^${f}\.qasm" --batch-size 1 --timeout 5400 --poll 30
done
echo ALL_DONE
