#!/bin/bash
# Run a Mocha-family JVM engine (external demo file loading) on every generated demo.
# Usage: run_java_matrix.sh <demo_dir> <label> <launcher_script> [jobs]; digests to <demo_dir>/_run/<label>_<demo>.txt
D=$1; LABEL=$2; LAUNCH=$3; J=${4:-6}; RUN=$D/_run
one() {
  d=$1; RUN=$2; LABEL=$3; LAUNCH=$4; mkdir -p $RUN/home_${LABEL}_$d; cd $RUN/home_${LABEL}_$d
  cp $RUN/DOOM1.WAD $RUN/$d.lmp . 2>/dev/null
  E13_DIGEST=$RUN/${LABEL}_$d.txt timeout 120 $LAUNCH -iwad DOOM1.WAD -timedemo $d -nodraw -nosound -nomusic > $RUN/${LABEL}_$d.log 2>&1
  cd $RUN; rm -rf $RUN/home_${LABEL}_$d
}
export -f one
ls $D/*.lmp | xargs -n1 basename | sed 's/.lmp$//' | xargs -P $J -I{} bash -c "one {} $RUN $LABEL $LAUNCH"
echo "done: $(ls $RUN/${LABEL}_g*.txt | wc -l) digests for $LABEL"
