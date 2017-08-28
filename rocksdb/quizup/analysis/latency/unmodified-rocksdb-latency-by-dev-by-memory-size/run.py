#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import ClientLogReader


def main(argv):
	with Cons.MT("Plotting ..."):
		# x: memory size
		# y: read latency
		# y: write latency in a separate plot

		env = os.environ.copy()
		in_fn = ClientLogReader.GetPlotDataFile()
		out_fn = "%s.pdf" % in_fn
		env["IN_FN"] = in_fn
		env["OUT_FN"] = out_fn

		Util.RunSubp("gnuplot %s/latency.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
