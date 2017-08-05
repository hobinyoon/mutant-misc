#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import LogReader


def main(argv):
	PlotLatency()


def PlotLatency():
	with Cons.MT("Plotting latency ..."):
		# Exploration of the effect of metadata caching
		# - Latency by metadata caching on and off by different storage devices
		# - Disk IOs by metadata caching on and off by different storage devices
		#
		# Storage usage and the # of compactions should be the same. It's an unmodified RocksDB.

		env = os.environ.copy()
		(in_fn, in_fn_individual)  = LogReader.GetFileLatencyByMetadataCachingByStgDevs()
		out_fn = "%s.pdf" % in_fn
		env["IN_FN"] = in_fn
		env["IN_FN_INDIVIDUAL"] = in_fn_individual
		env["OUT_FN"] = out_fn

		Util.RunSubp("gnuplot %s/latency.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
