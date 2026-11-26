#!/bin/bash
# Usage: run_demo.sh <engine_binary> <label> <demo1|demo2|demo3> [extra engine args...]
# Runs one shareware demo headless (SDL dummy drivers, timedemo) in a scratch HOME and writes <run>/<label>_<demo>.txt (per-tic digest) + .log
W=/srv/storage_16tb/projects/doom-e7-work/demo-study
ENGINE=$1; LABEL=$2; DEMO=$3; shift 3
RUN=${E13_RUN:-$W/run}; HOMEDIR=$RUN/home_$LABEL; mkdir -p $HOMEDIR
cd $RUN
HOME=$HOMEDIR XDG_DATA_HOME=$HOMEDIR XDG_CONFIG_HOME=$HOMEDIR LD_LIBRARY_PATH=$W/prefix/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  E13_DIGEST=$RUN/${LABEL}_${DEMO}.txt timeout ${E13_TIMEOUT:-120} $ENGINE -iwad $RUN/DOOM1.WAD -timedemo $DEMO -nodraw -nosound -nomusic -nogui "$@" > $RUN/${LABEL}_${DEMO}.log 2>&1
echo "$LABEL $DEMO rc=$? tics=$(wc -l < $RUN/${LABEL}_${DEMO}.txt 2>/dev/null)"
