#!/bin/bash

set -e
set -u
set -x

DN_YCSB=$HOME/work/mutant/YCSB

# TODO: will have to change on the EC2 instance. the symlinks.
DN_DB_DATA=$HOME/work/rocksdb-data/ycsb-d

rm -rf $DN_DB_DATA

pushd $DN_YCSB >/dev/null

echo "Loading the YCSB workload ..."
bin/ycsb load rocksdb \
  -P workloads/workloada \
  -s \
  -threads 100 \
  -p status.interval=1 \
  -p recordcount=5000000 \
  -p rocksdb.dir=$DN_DB_DATA

# Took 4 mins on mjolnir. 77GB of writes. Final DB size is 11GB.
#   -threads 20 \
#   -p recordcount=10000000 \ 10 M records

# Record size: 1 KB (defult value)
#
# # The number of fields in a record
# fieldcount=10
# # The size of each field (in bytes)
# fieldlength=100

popd >/dev/null
