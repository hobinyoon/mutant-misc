#! /bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/calc > /dev/null

#time ./build-and-run.sh --become_hotagain_temp_threshold=10
#time ./build-and-run.sh --become_hotagain_temp_threshold=20
#exit

for ((i=1; i<=16384; i*=2)); do
	printf "become_hotagain_temp_threshold: %.1f\n" $i
	time ./build-and-run.sh --become_hotagain_temp_threshold=$i
done

popd > /dev/null
