#!/usr/bin/env python

import math
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

_dn_stat = "%s/.stat" % os.path.dirname(__file__)
_dn_ycsb_log = "%s/work/mutant/log/ycsb" % os.path.expanduser("~")
_log_id = "160912-234955-d"
#_log_id = "160913-171610-d"
_fn_stat = None


def main(argv):
	GenPlotData()
	Plot()


def GenPlotData():
	with Cons.MT("Generating plot data ..."):
		Util.MkDirs(_dn_stat)

		global _fn_stat
		_fn_stat = "%s/%s" % (_dn_stat, _log_id)
		if os.path.isfile(_fn_stat):
			Cons.P("%s already exists" % _fn_stat)
			return

		fn_log = "%s/%s" % (_dn_ycsb_log, _log_id)
		sps = []

		with open(fn_log) as fo:
			# h0: header 0
			# h1: header 1
			# body : body
			loc = "h0"

			for line in fo.readlines():
				if loc == "h0":
					#Cons.P("%s" % line)
					if line.startswith("+ bin/ycsb run"):
						loc = "h1"
						continue
				elif loc == "h1":
					if line.startswith("DBWrapper: report latency for each error is false and specific error codes to track for latency are:"):
						loc = "body"
						continue
				elif loc == "body":
					if line.startswith("[OVERALL]"):
						loc = "tail"
						break
					sps.append(StatPerSec(line))

		timerange = sps[-1].timestamp - sps[0].timestamp

		# Reduce the output file size by skipping points that would overwrite on
		# existing points. For those points, the values are set to -1.
		#
		# Points within 1/400 of x-axis are considered to be too close.
		TIME_GRANULARITY_IN_SEC = int(timerange / 400)

		# We don't need separate IOPSes for read and write.
		#
		#IOPS_GRANULARITY_IN_LOG_E = 0.01
		#for i in range(len(sps)):
		#	if (i < TIME_GRANULARITY_IN_SEC):
		#		continue
		#	if sps[i].read_iops > 0:
		#		cur_read_iops = math.log(sps[i].read_iops, 10)
		#		for j in range(1, TIME_GRANULARITY_IN_SEC):
		#			if sps[i - j].read_iops > 0:
		#				if math.fabs(cur_read_iops - math.log(sps[i - j].read_iops, 10)) < IOPS_GRANULARITY_IN_LOG_E:
		#					sps[i].read_iops = -1
		#					break
		#	if sps[i].ins_iops > 0:
		#		cur_ins_iops = math.log(sps[i].ins_iops, 10)
		#		for j in range(1, TIME_GRANULARITY_IN_SEC):
		#			if sps[i - j].ins_iops > 0:
		#				if math.fabs(cur_ins_iops - math.log(sps[i - j].ins_iops, 10)) < IOPS_GRANULARITY_IN_LOG_E:
		#					sps[i].ins_iops = -1
		#					break

		iops_max = 0
		for s in sps:
			iops_max = max(iops_max, s.iops)
		IOPS_GRANULARITY = int(iops_max / 200)

		for i in range(len(sps)):
			if (i < TIME_GRANULARITY_IN_SEC):
				continue
			if sps[i].iops > 0:
				for j in range(1, TIME_GRANULARITY_IN_SEC):
					if sps[i - j].iops > 0:
						if math.fabs(sps[i].iops - sps[i - j].iops) < IOPS_GRANULARITY:
							sps[i].iops = -1
							break

		# Reduce overlapped points - latency
		#
		# Calculate max latency manually. There were 3 outliers as big as 350 ms.
		#lat_max = 0
		#for s in sps:
		#	lat_max = max(lat_max, s.read_lat_avg, s.ins_lat_avg)
		lat_max = 70000
		LAT_GRANULARITY = int(lat_max / 100)

		for i in range(len(sps)):
			if (i < TIME_GRANULARITY_IN_SEC):
				continue
			if sps[i].read_lat_avg > 0:
				for j in range(1, TIME_GRANULARITY_IN_SEC):
					if sps[i - j].read_lat_avg > 0:
						if math.fabs(sps[i].read_lat_avg - sps[i - j].read_lat_avg) < LAT_GRANULARITY:
							sps[i].read_lat_avg = -1
							break
			if sps[i].ins_lat_avg > 0:
				for j in range(1, TIME_GRANULARITY_IN_SEC):
					if sps[i - j].ins_lat_avg > 0:
						if math.fabs(sps[i].ins_lat_avg - sps[i - j].ins_lat_avg) < LAT_GRANULARITY:
							sps[i].ins_lat_avg = -1
							break

		with open(_fn_stat, "w") as fo:
			StatPerSec.WriteHeader(fo)
			for s in sps:
				fo.write("%s\n" % s)

		Cons.P("Created %s %d" % (_fn_stat, os.path.getsize(_fn_stat)))


def Plot():
	with Cons.MT("Plotting ..."):
		fn_in = _fn_stat
		fn_out = "%s/ycsb-iops-by-time-%s.pdf" % (_dn_stat, _log_id)
		env = os.environ.copy()
		env["FN_IN"] = fn_in
		env["FN_OUT"] = fn_out
		Util.RunSubp("gnuplot %s/ycsb-iops-by-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

		fn_in = _fn_stat
		fn_out = "%s/ycsb-lat-by-time-%s.pdf" % (_dn_stat, _log_id)
		env = os.environ.copy()
		env["FN_IN"] = fn_in
		env["FN_OUT"] = fn_out
		Util.RunSubp("gnuplot %s/ycsb-lat-by-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


class StatPerSec:
	fmt = "%5d %5d %8.2f %5d %8.2f %5d"

	def __init__(self, line):
		#Cons.P(line)
		# 2016-09-12 23:50:15:208 1 sec: 1950 operations; 1948.05 current ops/sec;
		# est completion in 14 hours 15 minutes [READ: Count=1842, Max=120063,
		# Min=6640, Avg=24343.08, 90=43007, 99=114687, 99.9=118527, 99.99=120063]
		# [INSERT: Count=112, Max=118655, Min=8216, Avg=25360.89, 90=43807,
		# 99=117951, 99.9=118655, 99.99=118655]
		mo = re.match(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d:\d\d\d (?P<timestamp>\d+) sec: \d+ operations; (\d|\.)+ current ops/sec; .+" \
				"READ: Count=(?P<read_iops>\d+), Max=\d+, Min=\d+, Avg=(?P<read_lat_avg>\S+) .+" \
				"INSERT: Count=(?P<ins_iops>\d+).+ Avg=(?P<ins_lat_avg>\S+)"
				, line)
		if mo is None:
			raise RuntimeError("Unexpected [%s]" % line)

		self.timestamp = int(mo.group("timestamp"))
		self.read_iops = int(mo.group("read_iops"))
		if self.read_iops == 0:
			self.read_lat_avg = 0
		else:
			try:
				self.read_lat_avg = float(mo.group("read_lat_avg")[:-1])
			except ValueError as e:
				Cons.P("%s [%s]" % (e, line))
				sys.exit(0)
		self.ins_iops = int(mo.group("ins_iops"))
		if self.ins_iops == 0:
			self.ins_lat_avg = 0
		else:
			self.ins_lat_avg = float(mo.group("ins_lat_avg")[:-1])
		self.iops = self.read_iops + self.ins_iops
	
	@staticmethod
	def WriteHeader(fo):
		fo.write("%s\n" % Util.BuildHeader(StatPerSec.fmt,
			"timestamp_in_sec"
			" read_iops"
			" read_lat_avg_in_us"
			" ins_iops"
			" ins_lat_avg_in_us"
			" iops"
			))

	def __str__(self):
		return StatPerSec.fmt % \
				(self.timestamp
						, self.read_iops
						, self.read_lat_avg
						, self.ins_iops
						, self.ins_lat_avg
						, self.iops
						)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
