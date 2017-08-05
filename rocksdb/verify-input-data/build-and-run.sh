#!/bin/bash

set -x
set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS > /dev/null

printf "Building ...\n"
time make -j

printf "\n"
printf "Running ...\n"
#time valgrind ./verify "$@"
time ./verify "$@"
