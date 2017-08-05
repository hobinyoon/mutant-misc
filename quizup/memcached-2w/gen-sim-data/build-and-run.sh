#! /bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`
DN_BUILD=$DN_THIS/target

printf "Building ...\n"
mkdir -p $DN_BUILD
pushd $DN_BUILD > /dev/null
cmake ..
#cmake -DCMAKE_BUILD_TYPE=Debug ..
time make -j
popd > /dev/null

printf "\n"
printf "Running ...\n"
#time valgrind target/gen "$@"
time target/gen "$@"
