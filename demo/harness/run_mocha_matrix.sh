#!/bin/bash
# Run Mocha Doom (Java) on every generated demo, digests into <demo_dir>/_run/moch_<demo>.txt. Usage: run_mocha_matrix.sh <demo_dir> [jobs]
W=/srv/storage_16tb/projects/doom-e7-work/demo-study
D=$1; J=${2:-6}; RUN=$D/_run
one() {
  d=$1; RUN=$2; W=$3; mkdir -p $RUN/home_moch_$d; cd $RUN/home_moch_$d
  cp $RUN/DOOM1.WAD $RUN/$d.lmp . 2>/dev/null
  E13_DIGEST=$RUN/moch_$d.txt timeout 120 xvfb-run -a java -cp $W/build/mochadoom/classes mochadoom.Engine -iwad DOOM1.WAD -timedemo $d -nodraw -nosound -nomusic > $RUN/moch_$d.log 2>&1
  cd $RUN; rm -rf $RUN/home_moch_$d
}
export -f one
ls $D/*.lmp | xargs -n1 basename | sed 's/.lmp$//' | xargs -P $J -I{} bash -c "one {} $RUN $W"
echo "done: $(ls $RUN/moch_*.txt | wc -l) digests"
