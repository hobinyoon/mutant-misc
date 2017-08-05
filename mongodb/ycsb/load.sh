#!/bin/bash

set -e
set -u
set -x

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/../.. >/dev/null
echo "Loading the YCSB workload ..."

SERVER_IP=`cat ~/work/mutant/.run/cassandra-server-ips`

# MongoDB doesn't need to create a DB or table.
#
# Clear existing DB to avoid the duplicate key error
#   com.mongodb.MongoWriteException: E11000 duplicate key error collection
/usr/bin/mongo $SERVER_IP/ycsb --eval="db.dropDatabase()"

time bin/ycsb load mongodb \
-P workloads/workloada \
-s \
-p mongodb.url=mongodb://$SERVER_IP \
-threads 10 \
-p recordcount=10000000

popd >/dev/null
