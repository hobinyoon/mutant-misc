#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import LogReader


def main(argv):
	with Cons.MT("Plotting ..."):
		# x: SSTable migration temperature threshold
		# y: read latency
		in_fn = LogReader.GetPlotDataFile()
		out_fn = "%s.pdf" % in_fn

		env = os.environ.copy()
		env["IN_FN"] = in_fn
		env["OUT_FN"] = out_fn

		Util.RunSubp("gnuplot %s/latency.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
