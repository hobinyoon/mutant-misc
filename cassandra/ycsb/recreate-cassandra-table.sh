#!/bin/bash

set -e
set -u
set -x

DN_THIS=`dirname $BASH_SOURCE`
CQLSH=$HOME/work/mutant/cassandra/bin/cqlsh

echo "(Re)creating the cassandra YCSB table ..."
$CQLSH -f $DN_THIS/recreate-cassandra-table.cql `cat ~/work/mutant/.run/cassandra-server-ips`
