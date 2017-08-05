#!/usr/bin/env python

import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Stat

_dn_stat = "%s/.stat" % os.path.dirname(__file__)


def main(argv):
	Util.MkDirs(_dn_stat)

	# Other logs in case needed
	#   128mb-seq-write-ebs-st1-160831-030914-c3.2xlarge
	#   128mb-seq-write-ebs-sc1-160831-031918-c3.2xlarge
	#   128mb-seq-write-ebs-gp2-160831-041249-c3.2xlarge
	#   128mb-seq-write-local-ssd-160831-034803-c3.2xlarge-80GB-before-initialization
	#   128mb-seq-write-local-ssd-160831-045917-c3.2xlarge-80GB-after-initialization
	#   128mb-seq-write-local-ssd-160831-050004-c3.2xlarge-80GB-after-initialization
	#
	#   128mb-seq-write-ebs-gp2-160831-155602-r3.xlarge-80GB-before-initialization
	#   128mb-seq-write-ebs-st1-160831-155935-r3.xlarge-80GB-before-initialization
	#   128mb-seq-write-local-ssd-160831-155328-r3.xlarge-80GB-before-initialization
	#   128mb-seq-write-ebs-sc1-160831-160311-r3.xlarge-80GB-before-initialization
	#   128mb-seq-write-local-ssd-160831-165303-r3.xlarge-80GB-after-initialization

	WriteStat([
			# Local SSD perf. Stick to the "after init" one.
			#
			# Underscore in _ is ugly, but gnuplot 4.6 doesn't support spaces.
			# - http://stackoverflow.com/questions/31654345/how-can-i-define-a-string-contain-space-array-in-gnuplot
			{"Local_SSD": "128mb-seq-write-local-ssd-160831-201951-c3.2xlarge-after-init"}
			# Note: May want to make a separate plot. before init, after init, after
			# full write.
			#, {"Local_SSD_before_init": "128mb-seq-write-local-ssd-160831-034803-c3.2xlarge-80GB-before-initialization"}
			#"Local SSD after init": "128mb-seq-write-local-ssd-160831-201951-c3.2xlarge-after-init"
			#, "Local SSD after init rewrite": "128mb-seq-write-local-ssd-160831-223155-c3.2xlarge-after-filling-up-the-volume"
			, {"EBS_gp2": "128mb-seq-write-ebs-gp2-160831-201951-c3.2xlarge"}
			, {"EBS_st1": "128mb-seq-write-ebs-st1-160831-201951-c3.2xlarge"}
			, {"EBS_sc1": "128mb-seq-write-ebs-sc1-160831-201951-c3.2xlarge"}
			])

	ReadStat(
			#[ {"Local_SSD": "4kb-read-local-ssd-160831-201951-c3.2xlarge-after-init"}
			##, {"Local_SSD_before_init": "4kb-read-local-ssd-c3.2xlarge"}
			#, {"EBS_gp2": "4kb-read-ebs-gp2-160831-201951-c3.2xlarge"}
			#, {"EBS_st1": "4kb-read-ebs-st1-160831-201951-c3.2xlarge"}
			#, {"EBS_sc1": "4kb-read-ebs-sc1-160831-201951-c3.2xlarge"}]

			#[ {"Local_SSD": "4kb-read-local-ssd-160901-225243-c3.2xlarge"}
			#, {"EBS_gp2":   "4kb-read-ebs-gp2-160901-225243-c3.2xlarge"}
			#, {"EBS_st1":   "4kb-read-ebs-st1-160901-225243-c3.2xlarge"}
			#, {"EBS_sc1":   "4kb-read-ebs-sc1-160901-225243-c3.2xlarge"}]

			#[ {"Local_SSD": "4kb-read-local-ssd-160901-230735-c3.2xlarge"}
			#, {"EBS_gp2":   "4kb-read-ebs-gp2-160901-230735-c3.2xlarge"}
			#, {"EBS_st1":   "4kb-read-ebs-st1-160901-230735-c3.2xlarge"}
			#, {"EBS_sc1":   "4kb-read-ebs-sc1-160901-230735-c3.2xlarge"}]

			#[ {"Local_SSD": "4kb-read-local-ssd-160901-231324-c3.2xlarge"}
			#, {"EBS_gp2":   "4kb-read-ebs-gp2-160901-231324-c3.2xlarge"}
			#, {"EBS_st1":   "4kb-read-ebs-st1-160901-231324-c3.2xlarge"}
			#, {"EBS_sc1":   "4kb-read-ebs-sc1-160901-231324-c3.2xlarge"}]

			[ {"Local SSD": "4kb-read-local-ssd-160902-130824-c3.2xlarge"}
			, {"EBS gp2":   "4kb-read-ebs-gp2-160902-130824-c3.2xlarge"}
			, {"EBS st1":   "4kb-read-ebs-st1-160902-130824-c3.2xlarge"}
			, {"EBS sc1":   "4kb-read-ebs-sc1-160902-130824-c3.2xlarge"}
			]
			)

class WriteStat():
	def __init__(self, logs):
		self.logs = logs
		for l in logs:
			self.GenStat(l.itervalues().next())
		self.PlotCDF()
		self.PlotByTime()

	def GenStat(self, fn):
		with Cons.MT(fn, print_time=False):
			thrp = []
			fn0 = "%s/result/%s" % (os.path.dirname(__file__), fn)
			with open(fn0) as fo:
				for line in fo.readlines():
					if line.startswith("1+0 records in"):
						continue
					if line.startswith("1+0 records out"):
						continue
					if line.startswith("real"):
						continue
					if line.startswith("user"):
						continue
					if line.startswith("sys"):
						continue

					# 134217728 bytes (134 MB) copied, 0.851289 s, 158 MB/s
					#m = re.match(r"\d+ bytes \(\d+ MB\) copied, (?P<lap_time>(\d|\.)+) s, .+", line)
					m = re.match(r"134217728 bytes \(134 MB\) copied, (?P<lap_time>(\d|\.)+) s, .+", line)
					if m:
						#Cons.P(m.group("lap_time"))
						thrp.append(128.0 / float(m.group("lap_time")))
						continue
					raise RuntimeError("Unexpected %s" % line)
			#Cons.P(len(thrp))
			Stat.GenStat(thrp, "%s/%s-cdf" % (_dn_stat, fn))

			# Throughput in the time order
			fn_time_order = "%s/%s-time-order" % (_dn_stat, fn)
			with open(fn_time_order, "w") as fo:
				for t in thrp:
					fo.write("%s\n" % t)
			Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

	def PlotCDF(self):
		with Cons.MT("Plotting 128mb write throughput CDF by storage ..."):
			fn_in = " ".join("%s/%s-cdf" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/128mb-write-thrp-cdf-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/seq-write-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTime(self):
		with Cons.MT("Plotting 128mb write throughput by time by storage ..."):
			fn_in = " ".join("%s/%s-time-order" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/128mb-write-thrp-by-time-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/seq-write-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


class ReadStat():
	def __init__(self, logs):
		with Cons.MT("Read stat:", print_time=False):
			self.logs = logs
			for l in logs:
				self.GenStat(l.itervalues().next())
			self.PlotCDF()
			# Hard to interprete with 4 different types
			#self.PlotByTimeByStorage()
			self.PlotByTime()

	def GenStat(self, fn):
		with Cons.MT(fn, print_time=False):
			lap_times = []
			fn0 = "%s/result/%s" % (os.path.dirname(__file__), fn)
			with open(fn0) as fo:
				for line in fo.readlines():
					line = line.rstrip()
					if len(line) == 0:
						continue

					# 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=1 time=219.1 us
					# 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=394 time=1.51 ms
					m = re.match(r"4 KiB from /mnt/.+/ioping-test-data \(ext4 /dev/xvd.\): request=\d+ time=(?P<lap_time>(\d|\.)+ (us|ms))", line)
					if m:
						lt = m.group("lap_time")
						if lt.endswith(" us"):
							lt = float(lt[:-3])
						elif lt.endswith(" ms"):
							lt = (float(lt[:-3]) * 1000)
						lap_times.append(lt)
						continue

					# --- /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb) ioping statistics ---
					if re.match(r"--- /mnt/.+/ioping-test-data \(ext4 /dev/xvd.\) ioping statistics ---", line):
						continue

					# 1 k requests completed in 175.1 ms, 3.91 MiB read, 5.71 k iops, 22.3 MiB/s
					# 1 k requests completed in 6.06 s, 3.91 MiB read, 164 iops, 659.8 KiB/s
					if re.match(r"\d+ k requests completed in .+ (min|s|ms|), .+ MiB read, .+ iops, .+ (K|M)iB/s", line):
						continue

					# min/avg/max/mdev = 146.9 us / 175.1 us / 1.77 ms / 79.6 us
					if re.match(r"min/avg/max/mdev = .+ (u|m)s / .+ (u|m)s / .+ (u|m)s / .+ (u|m)s", line):
						continue

					raise RuntimeError("Unexpected [%s]" % line)
			#Cons.P(len(lap_times))
			Stat.GenStat(lap_times, "%s/%s-cdf" % (_dn_stat, fn))

			# Throughput in the time order
			fn_time_order = "%s/%s-time-order" % (_dn_stat, fn)
			with open(fn_time_order, "w") as fo:
				for t in lap_times:
					fo.write("%s\n" % t)
			Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

	def PlotCDF(self):
		with Cons.MT("Plotting CDF by storage ..."):
			fn_in = " ".join("%s/%s-cdf" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/4kb-read-latency-cdf-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/rand-read-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTimeByStorage(self):
		with Cons.MT("Plotting by time by storage ..."):
			fn_in = " ".join("%s/%s-time-order" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			keys = " ".join(l.iterkeys().next().replace("_", "\\_") for l in self.logs)
			fn_out = "%s/4kb-read-latency-by-time-by-storages.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["KEYS"] = keys
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/rand-read-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTime(self):
		with Cons.MT("Plotting by time by storage ..."):
			i = 0
			for l in self.logs:
				i += 1
				fn_in = "%s/%s-time-order" % (_dn_stat, l.itervalues().next())
				key = l.iterkeys().next()
				fn_out = "%s/4kb-read-latency-by-time-%s.pdf" % (_dn_stat, key.replace(" ", "-"))

				env = os.environ.copy()
				env["FN_IN"] = fn_in
				env["KEY"] = key
				env["FN_OUT"] = fn_out
				env["KEY_IDX"] = str(i)
				env["Y_LABEL_COLOR"] = "black" if key == "Local SSD" else "white"
				Util.RunSubp("gnuplot %s/rand-read-by-time-single-storage.gnuplot" % os.path.dirname(__file__), env=env)
				Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
