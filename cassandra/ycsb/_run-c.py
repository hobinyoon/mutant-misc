#!/usr/bin/env python

import os
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	# No recreation of the keyspace. Use the pre-populated one.

	ycsb_params = ""
	if len(argv) > 1:
		ycsb_params = " ".join(argv[i] for i in range(1, len(argv)))
		# -p recordcount=1000 -p operationcount=1 -p status.interval=1 -p fieldcount=10 -p fieldlength=100
	else:
		ycsb_params += " -threads 100"

		# TODO: try these and see what the load is like
		ycsb_params += " -target 2000"

		ycsb_params += " -p recordcount=20000000"

		ycsb_params += " -p operationcount=50000000"

		ycsb_params += " -p status.interval=1"
		ycsb_params += " -p fieldcount=10"
		ycsb_params += " -p fieldlength=100"
		ycsb_params += " -p requestdistribution=uniform"
	Cons.P(ycsb_params)

	Cons.P("Running the YCSB workload ...")
	cmd = "cd %s/../.." \
			" && bin/ycsb run cassandra-cql" \
			" -P workloads/workloadc" \
			" -s" \
			% os.path.dirname(__file__)
			#" && bin/ycsb run basic" \
	
	# basic
	# "The YCSB Client is distributed with a simple dummy interface layer,
	# com.yahoo.ycsb.BasicDB. This layer just prints the operations it would have
	# executed to System.out. It can be useful for ensuring that the client is
	# operating properly, and for debugging your workloads."
	# [https://github.com/brianfrankcooper/YCSB/wiki/Running-a-Workload]

	fn_hosts = "%s/work/mutant/.run/cassandra-server-ips" % os.path.expanduser("~")
	if os.path.isfile(fn_hosts):
		cmd += (" -p hosts=`cat %s`" % fn_hosts)

	cmd += (" %s" % ycsb_params)

	Util.RunSubp(cmd, measure_time=True)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
