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
			" -P workloads/workloade" \
			" -s" \
			" -p hosts=`cat ~/work/mutant/.run/cassandra-server-ips`" \
			" %s" \
			% (os.path.dirname(__file__)
					, " ".join(argv[i] for i in range(1, len(argv))))
	Util.RunSubp(cmd, measure_time=True)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
