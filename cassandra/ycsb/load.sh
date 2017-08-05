#!/bin/bash

set -e
set -u
set -x

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

echo "Loading the YCSB workload ..."
bin/ycsb load cassandra-cql \
-P workloads/workloada \
-s \
-threads 10 \
-p hosts=`cat ~/work/mutant/.run/cassandra-server-ips` \
-p recordcount=1000

popd >/dev/null
