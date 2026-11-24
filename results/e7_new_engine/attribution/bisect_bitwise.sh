#!/usr/bin/env bash
# Which commit between #8939 (3c436c8c57) and the new engine changes chocolate-doom's function signals? Usage: bisect_bitwise.sh SHA ; prints 'GOOD' (same as C1 scan) or 'BAD'
export PATH=/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin:$PATH PYTHONDONTWRITEBYTECODE=1
P=${2:-chocolate-doom}
G=/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine-bisect; W=/srv/storage_16tb/projects/doom-e7-newengine-work/bis/$1
mkdir -p $W; git -C $G checkout -q --detach $1 || exit 9
python /srv/storage_16tb/projects/doom-dna-worktrees/e7-new-engine/measure_new_engine/scan_programs.py --engine $G --work $W --only $P > $W/scan_driver.log 2>&1
S=$(ls $W/scans); 
python - <<P2
import sys,json
sys.path.insert(0,'/srv/storage_16tb/projects/doom-dna-worktrees/e7-new-engine/measure_new_engine')
from compare_scans import compare
r=compare('/srv/storage_16tb/projects/doom-e7-newengine-work/c1/scans/3c436c8c5/$P/${P}_galaxy_master.db','$W/scans/'+'$S'+'/$P/${P}_galaxy_master.db')
print('GOOD' if r['functions_with_any_vector_input_diff']==0 and r['only_b']==0 else 'BAD', r['functions_with_any_vector_input_diff'], r['diff_signal_columns'])
P2
