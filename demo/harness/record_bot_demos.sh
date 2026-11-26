#!/bin/bash
# Record goal-directed bot demos with the bot-enabled reference build.
# Usage: record_bot_demos.sh <out_dir> [tics=6000] [seeds=4] [skill=3]
# Output: <out_dir>/gNNNN.lmp (+ gNNNN.meta: "map seed" and the bot's own summary lines) and a table bot_summary.csv
W=/srv/storage_16tb/projects/doom-e7-work/demo-study
OUT=$1; TICS=${2:-6000}; SEEDS=${3:-4}; SKILL=${4:-3}; mkdir -p $OUT/_rec
one() {
  OUT=$1; n=$2; map=$3; seed=$4; TICS=$5; SKILL=$6; W=/srv/storage_16tb/projects/doom-e7-work/demo-study
  d=$OUT/_rec/r$n; rm -rf $d; mkdir -p $d; cd $d; cp $W/run/DOOM1.WAD .
  name=$(printf "g%04d" $n)
  E13_BOT=1 E13_BOT_TICS=$TICS E13_BOT_SEED=$seed HOME=$d/h XDG_DATA_HOME=$d/h XDG_CONFIG_HOME=$d/h LD_LIBRARY_PATH=$W/prefix/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy E13_DIGEST=$d/rec.txt \
    timeout 600 $W/build/chocolate-bot/build/src/chocolate-doom -iwad DOOM1.WAD -skill $SKILL -warp 1 $map -nomonsters -record $name -nodraw -nosound -nomusic -nogui > bot.log 2>&1
  # validation: the recording must replay to exactly the same game (same digest), otherwise the demo is discarded
  HOME=$d/h XDG_DATA_HOME=$d/h XDG_CONFIG_HOME=$d/h LD_LIBRARY_PATH=$W/prefix/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy E13_DIGEST=$d/play.txt \
    timeout 600 $W/build/chocolate-bot/build/src/chocolate-doom -iwad DOOM1.WAD -timedemo $name -nodraw -nosound -nomusic -nogui > play.log 2>&1
  ok=0; [ -f $name.lmp ] && [ -s rec.txt ] && cut -d' ' -f2,3,5- rec.txt | head -n $(wc -l < play.txt) | cmp -s - <(cut -d' ' -f2,3,5- play.txt) && [ $(wc -l < rec.txt) -ge $(wc -l < play.txt) ] && ok=1
  [ $ok = 1 ] && cp $name.lmp $OUT/$name.lmp
  { echo "map=$map seed=$seed consistent=$ok"; grep "^BOT" bot.log | grep -E "done|opened|keys held|goal KEY"; } > $OUT/$name.meta
  rm -rf $d
}
export -f one
n=0; jobs=()
for map in 1 2 3 4 5 6 7 8 9; do for ((s=0; s<SEEDS; s++)); do jobs+=("$OUT $n $map $s $TICS $SKILL"); n=$((n+1)); done; done
printf "%s\n" "${jobs[@]}" | xargs -P 6 -L 1 bash -c 'one $0 $1 $2 $3 $4 $5'
echo "recorded: $(ls $OUT/g*.lmp | wc -l) demos"
