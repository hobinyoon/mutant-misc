#!/bin/bash

# ln -s ~/work/mutant/misc/misc/unzip-simulator-data.sh ~/work/quizup-data-zipped/unzip.sh

set -e
set -u
#set -x

dirs="0.05 0.10 1.00 10.00 100.00"
for dn in $dirs
do
	printf "Unzipping %s ...\n" $dn

	mkdir -p $HOME/work/quizup-data/memcached-2w/simulator-data/$dn

	tmpfile=$(mktemp /tmp/parallel.XXXXXX)
	for ((i=0; i<1000; i++)); do
		printf "7z e -o%s/work/quizup-data/memcached-2w/simulator-data/%s %s/%03d.7z >/dev/null\n" $HOME $dn $dn $i >> $tmpfile
	done

	parallel :::: $tmpfile
	rm $tmpfile
done

