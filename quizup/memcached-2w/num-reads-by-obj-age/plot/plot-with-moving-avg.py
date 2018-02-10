#!/usr/bin/env python

import datetime
import os
import sets
import sys
import time
import traceback

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser('~'))
import Cons
import Util


_fn_in  = "%s/work/quizup-data/memcached-2w/num-reads-by-obj-ages/num-reads-by-obj-age" % os.path.expanduser('~')
_dn_out = "%s/.output" % os.path.dirname(__file__)


def main(argv):
	Util.MkDirs(_dn_out)
	Plot()


def Plot():
	with Cons.MT("Plotting ..."):
		env = os.environ.copy()

		env["FN_IN"] = GetRunningAvg()
		env["NUM_OBJS"] = str(2047471)
		env["PER_OBJ"] = str(0)
		fn_out = "%s/quizup-num-reads-by-obj-age-aggregate.pdf" % _dn_out
		env["FN_OUT"] = fn_out

		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/num-reads-by-obj-ages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

		#env["PER_OBJ"] = str(1)
		#fn_out = "%s/quizup-num-reads-by-obj-age-per-obj.pdf" % _dn_out
		#env["FN_OUT"] = fn_out

		#with Cons.MT("Plotting ..."):
		#	Util.RunSubp("gnuplot %s/num-reads-by-obj-ages.gnuplot" % os.path.dirname(__file__), env=env)
		#	Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def GetRunningAvg():
	fn = "%s/num-reads-by-obj-age" % _dn_out
	if os.path.isfile(fn):
		return fn

	with Cons.MT("Generating running average ..."):
		# Running average of the last n items, not in the last n-minute time
		# window. Should generate smoother curve for plotting.
		q = Q(60)

		with open(_fn_in) as fo, open(fn, "w") as fo_out:
			for line in fo:
				t = line.strip().split(" ")
				if len(t) != 2:
					raise RuntimeError("Unexpected [%s]" % line)
				ts = int(t[0])
				num_reads = int(t[1])
				q.Enq(num_reads)

				if False:
					if ts < 2 * 24 * 60:
						fo_out.write("%d %d -\n" % (ts, num_reads))
					else:
						fo_out.write("%d %d %.1f\n" % (ts, num_reads, q.Avg()))
				else:
					fo_out.write("%d %d %.1f\n" % (ts, num_reads, q.Avg()))

		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
		return fn


# A simple, fast queue for single-threaded uses.
#
# Python Queue doesn't support getting exact size(). Interesting.
#   https://docs.python.org/2/library/queue.html
class Q:
	class ErrorEmpty:
		pass

	def __init__(self, capacity):
		self.capacity = capacity
		self.q = []
		# Dynamic sum
		self.sum = 0

	def Enq(self, e):
		if len(self.q) == self.capacity:
			self._Deq()

		self.q.append(e)
		self.sum += e

	def _Deq(self):
		if len(self.q) == 0:
			raise Q.ErrorEmpty()

		e = self.q[0]
		self.sum -= e

		# This can be O(n) if the list is array-based and does reorganization every
		# time. O(1), if a circular array.
		del self.q[0]
		return e

	def Avg(self):
		return float(self.sum) / len(self.q)


def Gen(fn_pair):
	try:
		start_time = time.time()

		# players_00433_20160726155140
		# 0123456789012345678901234567
		ts_lower = datetime.datetime.strptime(fn_pair[0][16:], "%y%m%d%H%M%S")
		if fn_pair[1] is None:
			ts_upper = None
		else:
			ts_upper = datetime.datetime.strptime(fn_pair[1][16:], "%y%m%d%H%M%S")

		ts_base = None

		fn1 = "%s/%s" % (_dn_in, fn_pair[0])
		fn_out = "%s/%s" % (_dn_out, fn_pair[0][16:22] + "-" + fn_pair[0][22:])
		ts_prev = None
		# Object IDs with the same timestamp
		obj_ids_w = sets.Set()
		obj_ids_r = sets.Set()
		num_skipped = 0
		with open(fn1) as fo_in, open(fn_out, "w") as fo_out:
			i = 0
			for line in fo_in:
				i += 1
				#if i % 10000 == 0:
				#	sys.stdout.write(".")
				#	sys.stdout.flush()
				t = line.strip().split(" ")
				if len(t) != 3:
					raise RuntimeError("Unexpected [%s]" % line)
				ts = float(t[0])
				if ts_base is None:
					ts_base = ts

				# When ts wraps around
				if (ts_prev is not None) and (ts < ts_prev):
					ts_base -= 4294

				ts1 = ts_lower + datetime.timedelta(seconds=(ts - ts_base))
				obj_id = t[2]
				op = t[1].replace("get", "G").replace("set", "S")

				# Skip timestamp not in the proper range. It happens due to the lack of
				# precision of the datetime in the file names.
				if (ts1 < ts_lower) or ((ts_upper is not None) and (ts_upper < ts1)):
					num_skipped += 1
					continue

				if ts != ts_prev:
					obj_ids_w.clear()
					obj_ids_r.clear()
					if op == "S":
						obj_ids_w.add(obj_id)
					elif op == "G":
						obj_ids_r.add(obj_id)

					fo_out.write("%s %s %s\n" % (ts1.strftime("%y%m%d-%H%M%S.%f"), op, obj_id))
					ts_prev = ts
				else:
					if op == "S":
						if obj_id not in obj_ids_w:
							fo_out.write("%s %s %s\n" % (ts1.strftime("%y%m%d-%H%M%S.%f"), op, obj_id))
							obj_ids_w.add(obj_id)
					elif op == "G":
						if obj_id not in obj_ids_r:
							fo_out.write("%s %s %s\n" % (ts1.strftime("%y%m%d-%H%M%S.%f"), op, obj_id))
							obj_ids_r.add(obj_id)

		Cons.P("Created %s %d in %.0f ms.%s" % \
				(fn_out, os.path.getsize(fn_out), (time.time() - start_time) * 1000.0, \
					((" Skipped %d due to out-of-order ts range" % num_skipped) if num_skipped > 0 else "")))

	except Exception as e:
		Cons.P("Error while processing %s\n%s\n%s\n" % (fn_pair[0], e, traceback.format_exc()))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
