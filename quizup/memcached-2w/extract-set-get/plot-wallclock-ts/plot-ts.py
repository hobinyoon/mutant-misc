#!/usr/bin/env python

import multiprocessing
import os
import re
import sys  
import time

from scapy.all import * 

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser('~'))
import Cons
import Util


def Extract(fn):
	fn_out = "%s/%s" % (_dn_out, os.path.splitext(os.path.basename(fn))[0])
	Cons.P("Extracing %s %d to %s" % (fn, os.path.getsize(fn), fn_out))

	pattern = re.compile("(?P<op>[sg]et) full-players:(?P<id>\d+)")

	with PcapReader(fn) as pr, open(fn_out, "w") as fo: 
		try:
			i = 0
			for p in pr:
				i += 1
				if i % 10000 == 0:
					sys.stdout.write(".")
					sys.stdout.flush()
					fo.flush()

				bp = bytes(p.payload)
				for m in pattern.finditer(bp):
					fo.write("%s %s %s\n" % (p.time, m.group("op"), m.group("id")))
		except Exception as e:
			sys.stderr.write("Error: %s\n" % format(e))
	
	Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


#def ClearLine():
#	sys.stdout.write("\033[1K") # Clear to the beginning of line
#	sys.stdout.write("\033[1G") # Move the cursor to the beginning of the column


_dn_in = "%s/data-set-get" % os.path.dirname(__file__)
_dn_out = "%s/data-set-get-wallclockts-wo-dup" % os.path.dirname(__file__)


def main(argv):
	Util.MkDirs(_dn_out)

	dt_fn = {}
	i = 0
	for f in os.listdir(_dn_in):
		if not f.startswith("players_"):
			continue
		# players_00433_20160726155140
		# 0123456789012345678901234567
		dt = f[14:]
		dt_fn[dt] = f
		i += 1
		if i == 3:
			break
	
	Cons.P("%d input files found" % len(dt_fn))

	dts = []
	fns = []
	for dt, fn in sorted(dt_fn.iteritems()):
		# 20160726155140
		# 01234567890123
		dt2 = dt[6:]
		dts.append(dt2)
		fns.append("%s/%s" % (_dn_in, fn))

	Plot(dts, fns)


def Plot(dts, fns):
	with Cons.MT("Plotting timestamp by files"):
		env = os.environ.copy()

		env["DTS"] = " ".join(dts)
		env["FNS"] = " ".join(fns)

		fn_out = "%s/timestamp-by-files.pdf" % _dn_out
		env["FN_OUT"] = fn_out

		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/timestamp-by-files.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
