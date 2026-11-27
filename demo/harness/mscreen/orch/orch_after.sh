#!/bin/bash
# Unattended end-of-night pipeline (owner asleep): waits for both main screens, then prboom-plus stage 1, baseline guard, registered analyses, prboom-plus stage 2, near-clone analyses.
cd /srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot
while [ ! -f /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/md_all.done ] || [ ! -f /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/choc_all.done ]; do sleep 60; done
date +%H:%M > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/after_started.txt
R=demo/harness/mscreen/runner.py; A=demo/harness/mscreen/analysis; O=/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/results/e15
PBR="/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/pb_v2 /srv/storage_16tb/projects/doom-e7-work/demo-study/screen/pb_phenotypes.sqlite --engine pb --clean /srv/storage_16tb/projects/doom-e7-work/demo-study/e14/clean/pb --maxload 20"
FUNCS=$(/srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I -c "import json; d=json.load(open('/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/pb_identical_functions.json')); print(','.join(d['identical']+d['near_identical']))")
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I $R $PBR --workers 12 --functions "$FUNCS" > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/pb_stage1.log 2>&1
/srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I demo/harness/mscreen/baselines.py verify > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/baselines_verify.log 2>&1
( nice -n 10 /srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I $A/run_e15.py $O > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis_primary.log 2>&1
  nice -n 10 /srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I $A/run_sensitivity.py $O > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis_sensitivity.log 2>&1
  nice -n 10 /srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I $A/run_exploratory.py $O > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis_exploratory.log 2>&1
  echo done > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis.done ) &
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I $R $PBR --workers 12 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/pb_stage2.log 2>&1
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I $R $PBR --workers 6 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/pb_rerun.log 2>&1
wait
nice -n 10 /srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I $A/pc2.py $O > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis_pc2.log 2>&1
nice -n 10 /srv/storage_16tb/projects/doom-e7-work/e11/venv/bin/python -I $A/run_cfamily.py $O > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/analysis_cfamily.log 2>&1
echo done > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/pb_all.done
