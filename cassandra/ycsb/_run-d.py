#!/usr/bin/env python

import os
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	Util.RunSubp("%s/recreate-cassandra-table.sh" % os.path.dirname(__file__))
	time.sleep(0.1)

	Util.RunSubp("%s/load.sh" % os.path.dirname(__file__))
	time.sleep(0.1)

	Cons.P("Running the YCSB workload ...")
	cmd = "cd %s/../.." \
			" && bin/ycsb run cassandra-cql" \
			" -P workloads/workloadd" \
			" -s" \
			" -p hosts=`cat ~/work/mutant/.run/cassandra-server-ips`" \
			" %s" \
			% (os.path.dirname(__file__)
					, " ".join(argv[i] for i in range(1, len(argv))))
	Util.RunSubp(cmd, measure_time=True)


# Just a note of how I ran workload d
def Note():
	ycsb_params = \
			" -threads 100" \
			" -p recordcount=1000" \
			" -p status.interval=1" \
			" -p fieldcount=10" \
			" -p fieldlength=100"

	# 20 M, 1KB, 50% write requests = 10 GB
	# 400 M, 1KB, 5% write requests = 20 GB
	#
	# It takes a long time. Keep a snapshot of the data and the commit log
	# directories for later.
	ycsb_params += " -p operationcount=400000000"

	# Generate SSTables a bit faster. The default was 95% read.
	#ycsb_params += " -p readproportion=0.50 -p insertproportion=0.50"
	#
	# 30% writes to reduce the pending compactions. With a 50% write, network
	# BW was less than 15 MB/sec. Still pending compactions. Max network
	# bandwidth recv/send: 26 MB/13 MB
	#
	# With 20% write, up to 4 after 500 secs. Max network bandwidth 38 / 20 MB
	# But, the number goes down.
	#ycsb_params += " -p readproportion=0.80 -p insertproportion=0.20"
	#
	# 15% writes. Unthrottling is still not very realistic. The average server
	# load at Google is less than 30%. Max network 43 / 10. Up to 3.
	# I don't see any intra-L0 compactions.
	#ycsb_params += " -p readproportion=0.85 -p insertproportion=0.15"

	ycsb_params += " -p readproportion=0.95 -p insertproportion=0.05"

	# Throttle
	# With 10K, server CPU load less than 20%. It spikes to 40% when
	# compacting.
	# With 12K, about the same.
	# 20K. About 40%
	# 17K.
	#   About 31 - 32%. Good. 37% at 1000 secs. 50% at 2000 secs. 50 - 60% at
	#   8000 secs.
	#   Took 33974804 ms = 9 h 26 m
	#   Data and commit log directory sizes:
	#     13596    /home/ubuntu/work/mutant/cassandra/data/commitlog
	#     4        /home/ubuntu/work/mutant/cassandra/data/hints
	#     58596    /home/ubuntu/work/mutant/cassandra/data/saved_caches
	#     21240284 /mnt/local-ssd1/cassandra-data
	#   Number of SSTables in /mnt/local-ssd1/cassandra-data/ycsb/usertable-488da08084bf11e6ad9963c053f92bbd:
	#     146
	ycsb_params += " -target 17000"

	# Can you skip the loading phase? Probably by starting from 0 record?
	# Not progressing. A CPU seems to be stalled. Let's not do this. With 1
	# record loaded, it shows the READ-FAILED stat.
	#"-p recordcount=0" \

	# 16 GB. Makes sense. Raw data is about 10 GB.
	#" -p operationcount=10,000,000" \
	#" -p fieldcount=10" \
	#" -p fieldlength=100" \

	# Without limiting memory, p fieldcount=10 fieldlength=100 -threads 100, server CPU is the
	# bottleneck. Network around 52 MB/s.
	#
	# With a 2GB memory,
	#   -p fieldlength=10000, network
	#     becomes the bottleneck. 125 MB/sec
	#   -p fieldlength=400
	#     In 6 mins, network IO drops below 40 MB/sec
	#   -p fieldlength=1000. record size is 10 KB
	#     the same. But, in 3 mins, the bottleneck becomes the disk IO.
	#   -p fieldlength=2000. record size is 20 kb
	#     the same. but, in 230 secs, the bottleneck becomes the disk io.
	#     todo: sstables are growing so fast. looks like the total will be around 20 gb. good!
	#   -p fieldlength=100. record size is 1 kb
	#     the same. but, in 230 secs, the bottleneck becomes the disk io.


if __name__ == "__main__":
	sys.exit(main(sys.argv))
