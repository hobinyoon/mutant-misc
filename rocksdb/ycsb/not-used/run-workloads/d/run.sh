#!/bin/bash

set -e
set -u
set -x

DN_YCSB=$HOME/work/mutant/YCSB

pushd $DN_YCSB >/dev/null

echo "Running the YCSB workload ..."
# Took 2 mins on mjolnir without memory capping. The system was super busy.
bin/ycsb run rocksdb \
  -P workloads/workloadd \
  -s \
  -threads 100 \
  -p status.interval=1 \
  -p recordcount=10000000 \
  -p operationcount=1000000 \
  -p rocksdb.dir=$HOME/work/rocksdb-data/ycsb-d \
  -p readproportion=0.95 \
  -p insertproportion=0.05 \

#-threads 10 \
#-p status.interval=1 \
#-p recordcount=10000000 \
#-p operationcount=1000 \
#-p rocksdb.dir=$HOME/work/rocksdb-data \
#-target 1

popd >/dev/null
