#!/usr/bin/env bash
# DOOM-E7 replication: the registered order of operations on one work dir (one engine's scans).
#   bash run_pipeline.sh TAG ENGINE_SHORT STAGE      STAGE = A (phase A + arbiter + analysis), B (phase B + report), A2 (pooled K=25 draws + analyses)
# TAG = new | c0 | c1 (work dir /srv/storage_16tb/projects/doom-e7-newengine-work/TAG). Scans must be finished.
# Each stage logs to WORK/logs. Python: the selfscan venv. Heavy stage (A2 draws) runs through heavy-run.sh.
set -u
TAG=$1; ENG=$2; STAGE=${3:?stage A, B or A2}
export PATH=/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
M=/srv/storage_16tb/projects/doom-dna-worktrees/e7-new-engine/measure_new_engine
B=/srv/storage_16tb/projects/doom-e7-newengine-work
export E7_WORK=$B/$TAG E7_ENGINE=$ENG
HEAVY=/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine-current/tests/tools/box/heavy-run.sh
L=$B/logs; mkdir -p $L
run() { local name=$1; shift; echo "$(date +%T) $name: $*" >> $L/${TAG}_commands.txt; "$@" > $L/${TAG}_$name.log 2>&1 || { echo "STAGE $name FAILED rc=$?" | tee -a $L/${TAG}_pipeline.log; return 1; }; echo "$(date +%T) $name done" >> $L/${TAG}_pipeline.log; }
MAPS=$(python - <<P
import json
p=json.load(open('/srv/storage_16tb/projects/doom-dna-worktrees/e7-new-engine/manifest/RUN_PINS.json'))['programs']
print(','.join(x['name'] for x in p if x['role'] in ('map','map-negative-unrelated','map-negative-same-studio')))
P
)
# the text arbiter reads function bodies from source trees: rebuild them (without .git/.gitgalaxy) from the frozen clones
mkdir -p $E7_WORK/repos
for n in ${MAPS//,/ }; do [ -d $E7_WORK/repos/$n ] || rsync -a --exclude=.git --exclude=.gitgalaxy /srv/storage_16tb/projects/doom-e7-work/repos/$n/ $E7_WORK/repos/$n/; done
if [ "$STAGE" = A ]; then
run phaseA python $M/e7_run.py --phase A --workers 3 || exit 1
run arbiter python $M/e7_arbiter.py --work $E7_WORK --engine $ENG --ports $MAPS --out $E7_WORK/results/e7/phaseA/arbiter || exit 1
run analyze python $M/e7_analyze.py || exit 1
fi
if [ "$STAGE" = B ]; then
run phaseB python $M/e7_run.py --phase B --workers 3 || exit 1
run phaseBreport python $M/e7_phaseb.py || exit 1
fi
if [ "$STAGE" = A2 ]; then
  run a2draws $HEAVY python $M/e7_draws.py --work $E7_WORK --out $B/${TAG}_a2 --k 25 --workers 3 || exit 1
  for v in primary conservative; do
    E7_WORK=$B/${TAG}_a2/$v run a2analyze_$v python $M/e7_analyze.py || exit 1
  done
  O=/srv/storage_16tb/projects/doom-e7-work/results/e7/phaseA
  run a2summary python $M/a2_summary.py --single $E7_WORK/results/e7/phaseA --a2 $B/${TAG}_a2 --fixed-from $O --json $B/${TAG}_a2/a2_summary.json || exit 1
  E7_A2=$B/${TAG}_a2 E7_SUPP_OUT=$B/${TAG}_a2/SUPPLEMENT_S-A.md run supp python $M/e7_supp_table.py
fi
echo "$(date +%T) pipeline $TAG finished" >> $L/${TAG}_pipeline.log
