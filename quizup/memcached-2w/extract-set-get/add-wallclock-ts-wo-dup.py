#!/usr/bin/env python

import datetime
import multiprocessing
import os
import sets
import sys  
import time
import traceback

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser('~'))
import Cons
import Util


_dn_in  = "%s/work/quizup-data/memcached-2w/data-set-get" % os.path.expanduser('~')
_dn_out = "%s/work/quizup-data/memcached-2w/data-set-get-wallclockts-no-dup" % os.path.expanduser('~')


def main(argv):
	Util.MkDirs(_dn_out)

	i = 0
	dt_fn = {}
	for fn in os.listdir(_dn_in):
		if not fn.startswith("players_"):
			continue
		# players_00433_20160726155140
		# 0123456789012345678901234567
		dt = fn[16:]
		dt_fn[dt] = fn
		# Useful for debugging
		if False:
			i += 1
			if i == 3:
				break
	Cons.P("%d input files found" % len(dt_fn))

	# [ (fn, fn_next) ]
	#   the last one has fn_next None
	fns2 = []
	fn_prev = None
	for dt, fn in sorted(dt_fn.iteritems()):
		if fn_prev is None:
			fn_prev = fn
			continue
		fns2.append((fn_prev, fn))
		fn_prev = fn
	fns2.append((fn_prev, None))

	p = multiprocessing.Pool()
	p.map(Gen, fns2)


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
