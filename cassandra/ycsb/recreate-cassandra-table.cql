-- cqlsh -f create-cassandra-table.cql `cat ~/work/mutant/.run/cassandra-server-ips`

-- https://github.com/brianfrankcooper/YCSB/tree/master/cassandra

drop keyspace if exists ycsb;

create keyspace ycsb
WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 1 };

USE ycsb;

create table usertable (
		y_id varchar primary key,
		field0 varchar,
		field1 varchar,
		field2 varchar,
		field3 varchar,
		field4 varchar,
		field5 varchar,
		field6 varchar,
		field7 varchar,
		field8 varchar,
		field9 varchar)
with compaction =
    { 'class' : 'LeveledCompactionStrategy'
		, 'log_all' : true
		};
--		, 'sstable_size_in_mb' : 20

-- SSTable size to 20 MB just for checking how SSTables are compacted.
-- - https://docs.datastax.com/en/cql/3.1/cql/cql_reference/compactSubprop.html
