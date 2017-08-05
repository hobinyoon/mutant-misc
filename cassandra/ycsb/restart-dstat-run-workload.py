#!/usr/bin/env python

import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib" % os.path.expanduser("~"))
import Ec2Util


_cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

def main(argv):
	RestartDstat()
	RunYcsb(argv)
	StopDstat()


def RunYcsb(argv):
	dn_ycsb_log = "%s/work/mutant/log/%s/%s/ycsb" \
			% (os.path.expanduser("~"), Ec2Util.JobId(), Ec2Util.NodeName())
	Util.MkDirs(dn_ycsb_log)

	if len(argv) >= 3:
		workload_type = argv[1]
		ycsb_params = " ".join(argv[i] for i in range(2, len(argv)))
	else:
		workload_type = "c"
		ycsb_params = " ".join(argv[i] for i in range(2, len(argv)))

	fn_log = "%s/%s-%s" % (dn_ycsb_log, _cur_datetime, workload_type)

	cmd = "%s/_run-%s.py %s 2>&1 | tee -a %s | grep --color=always -E \"^|Mutant\"" \
			% (os.path.dirname(__file__), workload_type, ycsb_params, fn_log)
	Util.RunSubp(cmd)
	Cons.P("Created %s %d" % (fn_log, os.path.getsize(fn_log)))


_region = None
def GetRegion():
	global _region
	if _region is not None:
		return _region

	# http://stackoverflow.com/questions/4249488/find-region-from-within-ec2-instance
	doc       = Util.RunSubp("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document", print_cmd = False, print_output = False)
	for line in doc.split("\n"):
		# "region" : "us-west-1"
		tokens = filter(None, re.split(":| |,|\"", line))
		#Cons.P(tokens)
		if len(tokens) == 2 and tokens[0] == "region":
			_region = tokens[1]
			return _region


_inst_id = None
def InstId():
	global _inst_id
	if _inst_id is not None:
		return _inst_id

	_inst_id  = Util.RunSubp("curl -s http://169.254.169.254/latest/meta-data/instance-id", print_cmd = False, print_output = False)
	return _inst_id


# May want to make it an object and use RAII
def RestartDstat():
	with Cons.MT("Restarting dstat ...", print_time=False):
		cmd = "ps -e -o pid,ppid,user,args"
		lines = Util.RunSubp(cmd, print_cmd=False, print_output=False)
		#Cons.P(lines)
		pids = []
		for line in lines.split("\n"):
			line = line.strip()
			if "dstat" not in line:
				continue
			if "csv" not in line:
				continue

			# Get the second-level processes, skipping the root-level ones.
			t = re.split(" +", line)
			if t[1] == "1":
				continue
			pids.append(t[0])
			#Cons.P("[%s]" % line)

		if len(pids) > 0:
			#Cons.P("[%s]" % " ".join(pids))
			Util.RunSubp("kill %s" % " ".join(pids))

			# Make sure each of the processes has terminated
			for pid in pids:
				cmd = "kill -0 %s" % pid
				while True:
					r = 0
					with open(os.devnull, "w") as devnull:
						r = subprocess.Popen(cmd, shell=True, stdin=devnull, stdout=devnull, stderr=devnull)
					if r != 0:
						Cons.P("Process %s has terminated" % pid)
						break
					time.sleep(0.1)

		# Run dstat as a daemon
		dn = "%s/work/mutant/log/%s/%s/dstat" \
				% (os.path.expanduser("~"), Ec2Util.JobId(), Ec2Util.NodeName())
		Util.MkDirs(dn)

		fn_out = "%s/%s.csv" % (dn, _cur_datetime)
		cmd = "dstat -tcdn -C total -D xvda,xvdb,xvdd,xvde,xvdf -r --output %s" % fn_out
		Util.RunDaemon(cmd)


def StopDstat():
	with Cons.MT("Stopping dstat ...", print_time=False):
		cmd = "ps -e -o pid,ppid,user,args"
		lines = Util.RunSubp(cmd, print_cmd=False, print_output=False)
		#Cons.P(lines)
		pids = []
		for line in lines.split("\n"):
			line = line.strip()
			if "dstat" not in line:
				continue
			if "csv" not in line:
				continue

			# Get the second-level processes, skipping the root-level ones.
			t = re.split(" +", line)
			if t[1] == "1":
				continue
			pids.append(t[0])
			#Cons.P("[%s]" % line)

		if len(pids) > 0:
			#Cons.P("[%s]" % " ".join(pids))
			Util.RunSubp("kill %s" % " ".join(pids))

			# Make sure each of the processes has terminated
			for pid in pids:
				cmd = "kill -0 %s" % pid
				while True:
					r = 0
					with open(os.devnull, "w") as devnull:
						r = subprocess.Popen(cmd, shell=True, stdin=devnull, stdout=devnull, stderr=devnull)
					if r != 0:
						Cons.P("Process %s has terminated" % pid)
						break
					time.sleep(0.1)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
