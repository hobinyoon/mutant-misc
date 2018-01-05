#!/bin/bash

fn_out=$1

pid0=`pgrep -x java`
#pid=`pgrep java | awk '{printf "%s", $1}'`

if [ ! -z "$pid0" ]; then
  #printf "pid0=[%s]\n" $pid0
  printf "%s " `date +%y%m%d-%H%M%S` >> $fn_out
  cat /proc/$pid0/statm >> $fn_out
fi
