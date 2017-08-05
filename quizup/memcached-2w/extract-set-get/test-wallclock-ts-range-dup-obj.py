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


_dn_in = "%s/work/quizup-data/memcached-2w/data-set-get-wallclockts-no-dup" % os.path.expanduser('~')


def main(argv):
	i = 0
	fns = []
	for fn in os.listdir(_dn_in):
		fns.append(fn)
		# Useful for debugging
		if False:
			i += 1
			if i == 1:
				break
	Cons.P("%d input files found" % len(fns))
	fns.sort()

	# [ (fn, fn_next) ]
	#   the last one has fn_next None
	fns2 = []
	for i in range(len(fns)):
		if i < len(fns) - 1:
			fns2.append((fns[i], fns[i+1]))
		else:
			fns2.append((fns[i], None))

	p = multiprocessing.Pool()
	p.map(Check, fns2)


def Check(fn_pair):
	try:
		start_time = time.time()

		# 160718-144303
		ts_lower = fn_pair[0]
		if fn_pair[1] is None:
			ts_upper = None
		else:
			ts_upper = fn_pair[1]

		fn1 = "%s/%s" % (_dn_in, fn_pair[0])

		ts_prev = None
		# Object IDs with the same timestamp
		obj_ids_w = sets.Set()
		obj_ids_r = sets.Set()

		with open(fn1) as fo:
			for line in fo:
				line = line.strip()
				t = line.split(" ")
				if len(t) != 3:
					raise RuntimeError("Unexpected [%s]" % line)
				ts = t[0]
				op = t[1].replace("get", "G").replace("set", "S")
				obj_id = t[2]

				if (ts < ts_lower) or ((ts_upper is not None) and (ts_upper < ts)):
					#Cons.P("ts_lower ts_upper ts %s %s %s" \
					#		% (ts_lower, ts_upper, ts))
					raise RuntimeError("Unexpected: ts_lower ts_upper ts %s %s %s" \
							% (ts_lower, ts_upper, ts))

				if (ts_prev is not None) and (ts < ts_prev):
					raise RuntimeError("Unexpected: ts_prev ts %s %s" % (ts_prev, ts))

				if ts != ts_prev:
					obj_ids_w.clear()
					obj_ids_r.clear()
					if op == "S":
						obj_ids_w.add(obj_id)
					elif op == "G":
						obj_ids_r.add(obj_id)
					ts_prev = ts
				else:
					if op == "S":
						if obj_id in obj_ids_w:
							raise RuntimeError("Unexpected: [%s]" % line)
						obj_ids_w.add(obj_id)
					elif op == "G":
						if obj_id in obj_ids_r:
							raise RuntimeError("Unexpected: [%s]" % line)
						obj_ids_r.add(obj_id)

		Cons.P("Checked %s %d in %.0f ms" % \
				(fn1, os.path.getsize(fn1), (time.time() - start_time) * 1000.0))

	except Exception as e:
		Cons.P("Error while checking %s\n%s\n%s\n" % (fn1, e, traceback.format_exc()))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
