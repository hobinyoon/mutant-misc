#!/bin/bash

set -e
set -u

plot() {
	echo "Plotting ..."
	export FN_IN=$1
	export FN_OUT=$2
	gnuplot ./key-dist-by-time.gnuplot | sed 's/^/  /'
	if [ "${PIPESTATUS[0]}" -ne "0" ]; then
		exit 1
	fi
	printf "  Created %s %d\n" $FN_OUT `wc -c < $FN_OUT`
}

DN_THIS=`dirname $BASH_SOURCE`
pushd $DN_THIS >/dev/null

# Note: parallelize when needed

plot "data-key-distribution-with-requestdistribution-uniform" "uniform-by-time.pdf"
plot "data-key-distribution-with-requestdistribution-zipfian" "zipfian-by-time.pdf"

popd >/dev/null
