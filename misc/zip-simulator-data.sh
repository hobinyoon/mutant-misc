#!/bin/bash

# ln -s ~/work/mutant/misc/misc/zip-simulator-data.sh ~/work/quizup-data/memcached-2w/simulator-data/zip.sh

set -e
set -u

tmpfile=$(mktemp /tmp/parallel.XXXXXX)

for ((i=0; i<1000; i++)); do
	printf "7z a -mx %03d.7z %03d >/dev/null\n" $i $i >> $tmpfile
done
#cat $tmpfile

set -x

dirs="0.05 0.10 1.00 10.00 100.00"
for dn in $dirs
do
	printf "Zipping %s ...\n" $dn
	pushd $dn
	parallel :::: $tmpfile
	popd
	mv $dn/*.7z $HOME/work/quizup-data-zipped/$dn
done

rm $tmpfile
