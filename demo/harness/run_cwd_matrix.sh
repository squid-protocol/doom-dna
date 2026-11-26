#!/bin/bash
# Run an engine that reads files relative to its working directory (e.g. gore) on every generated demo.
# Env: E13_ARGS overrides the engine arguments (default is the doomgeneric-style timedemo line).
# Usage: run_cwd_matrix.sh <demo_dir> <label> <engine_binary> [jobs] [timeout_s]; digests to <demo_dir>/_run/<label>_<demo>.txt
D=$1; LABEL=$2; ENGINE=$3; J=${4:-6}; TO=${5:-8}; RUN=$D/_run
one() {
  d=$1; RUN=$2; LABEL=$3; ENGINE=$4; TO=$5; mkdir -p $RUN/home_${LABEL}_$d; cd $RUN/home_${LABEL}_$d
  python3 /srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/make_demo_iwad.py $RUN/DOOM1.WAD $RUN/$d.lmp ./DEMOIWAD.WAD
  E13_DIGEST=$RUN/${LABEL}_$d.txt timeout $TO $ENGINE ${E13_ARGS:--iwad DEMOIWAD.WAD -timedemo demo1 -nodraw -nosound -nomusic} > /dev/null 2>&1
  cd $RUN; rm -rf $RUN/home_${LABEL}_$d
}
export -f one; export E13_ARGS
ls $D/*.lmp | xargs -n1 basename | sed 's/.lmp$//' | xargs -P $J -I{} bash -c "one {} $RUN $LABEL $ENGINE $TO"
echo "done: $(ls $RUN/${LABEL}_g*.txt | wc -l) digests for $LABEL"
