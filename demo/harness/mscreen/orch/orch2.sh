#!/bin/bash
cd /srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot
M="/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/md_v2 /srv/storage_16tb/projects/doom-e7-work/demo-study/screen/md_phenotypes.sqlite --engine md --clean /srv/storage_16tb/projects/doom-e7-work/demo-study/e14/clean/md --maxload 20"
C="/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/choc_v2 /srv/storage_16tb/projects/doom-e7-work/demo-study/screen/choc_phenotypes.sqlite --maxload 20"
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $M --workers 9 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/md_rerun_main.log 2>&1 &
PM=$!
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $C --workers 12 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/screen_choc_v2c.log 2>&1 &
PC=$!
( while kill -0 $PM 2>/dev/null; do sleep 20; done
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $M --workers 4 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/md_rerun_a.log 2>&1
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $M --workers 8 --refresh-profile > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/screen_md_f.log 2>&1
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $M --workers 4 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/md_rerun_f.log 2>&1
  echo done > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/md_all.done ) &
( while kill -0 $PC 2>/dev/null; do sleep 20; done
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $C --workers 8 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/choc_rerun_v2.log 2>&1
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py /srv/storage_16tb/projects/doom-e7-work/demo-study/screen/choc /srv/storage_16tb/projects/doom-e7-work/demo-study/screen/choc_phenotypes.sqlite --maxload 20 --workers 8 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/choc_rerun_old.log 2>&1
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $C --workers 12 --refresh-profile > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/screen_choc_f.log 2>&1
  /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python -I demo/harness/mscreen/runner.py $C --workers 8 --rerun-hangs --timeout 60 > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/choc_rerun_f.log 2>&1
  echo done > /srv/storage_16tb/projects/doom-e7-work/demo-study/logs/choc_all.done ) &
wait
