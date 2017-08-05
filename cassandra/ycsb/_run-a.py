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
	if True:
		ycsb_params = " ".join(argv[i] for i in range(1, len(argv)))
		# -p recordcount=1000 -p operationcount=1 -p status.interval=1 -p fieldcount=10 -p fieldlength=100
	else:
		ycsb_params += " -threads 100"

		# The server can handle >6000 IOPS when unthrottled
		# With 4000, server CPU load < 20%
		#
		# CPU up to 47%, when running multiple compactions.
		ycsb_params += " -target 4000"

		ycsb_params += " -p recordcount=20000000"

		# 100000 : 27736.0 ms = ? : 1 h
		#ycsb_params += " -p operationcount=100000"
		# 12979521 operations to run for 1 hour.
		#ycsb_params += " -p operationcount=12979521"
		# For 10 hours
		ycsb_params += " -p operationcount=129795210"

		ycsb_params += " -p status.interval=1"
		ycsb_params += " -p fieldcount=10"
		ycsb_params += " -p fieldlength=100"
	Cons.P(ycsb_params)

	Cons.P("Running the YCSB workload ...")
	cmd = "cd %s/../.." \
			" && bin/ycsb run cassandra-cql" \
			" -P workloads/workloada" \
			" -s" \
			" -p hosts=`cat ~/work/mutant/.run/cassandra-server-ips`" \
			" %s" \
			% (os.path.dirname(__file__), ycsb_params)
	Util.RunSubp(cmd, measure_time=True)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
