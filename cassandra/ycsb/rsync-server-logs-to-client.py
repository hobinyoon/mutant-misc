#!/usr/bin/env python

import os
import socket
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	# $ tree -d /mnt/local-ssd0/mutant/log
	# .
	# `-- 161031-214118
	#     :-- c
	#     :   |-- dstat
	#     :   `-- ycsb
	#     `-- s0 (copied from s0)
	#         :-- cassandra
	#         `-- dstat

	exp_id = JobId()

	# For now, assume only one IP. Update when there are multiple IPs.
	if len(ServerIPs()) != 1:
		raise RuntimeError("Unexpected")
	s0_ip = ServerIPs()[0]

	# dstat logs are already in the log directory of the server
	cmd = "rsync -avP ubuntu@%s:/mnt/local-ssd0/mutant/log/%s/* /mnt/local-ssd0/mutant/log/%s/" \
			% (s0_ip, exp_id, exp_id)
	Util.RunSubp(cmd, measure_time=True)

	# Get Cassandra logs too
	dn = "/mnt/local-ssd0/mutant/log/%s/s0/cassandra" % exp_id
	Util.MkDirs(dn)
	cmd = "rsync -avP ubuntu@%s:work/mutant/cassandra/logs/* %s/" \
			% (s0_ip, dn)
	Util.RunSubp(cmd, measure_time=True)


_job_id = None

def JobId():
	global _job_id
	if _job_id is not None:
		return _job_id

	hn = socket.gethostname()
	t = hn.split("-")
	_job_id = t[3] + "-" + t[4]
	return _job_id


_server_ips = None
def ServerIPs():
	global _server_ips
	if _server_ips is not None:
		return _server_ips

	fn = "%s/work/mutant/.run/cassandra-server-ips" % os.path.expanduser("~")
	with open(fn) as fo:
		_server_ips = []
		for line in fo.readlines():
			_server_ips.append(line.strip())
	return _server_ips


if __name__ == "__main__":
	sys.exit(main(sys.argv))
