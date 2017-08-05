#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import LogReader


def main(argv):
	dn = "%s/.output" % os.path.dirname(__file__)
	Util.MkDirs(dn)

	PlotRocksDbMutantLatency()


def PlotRocksDbMutantLatency():
	in_fn_rocksdb = LogReader.GetRocksDbCostLatencyDataFile()
	in_fn_mutant = LogReader.GetMutantCostLatencyDataFile()
	out_fn = "%s/.output/rocksdb-2level-mutant-latency.pdf" % os.path.dirname(__file__)

	with Cons.MT("Plotting ..."):
		env = os.environ.copy()
		env["IN_FN_ROCKSDB"] = in_fn_rocksdb
		env["IN_FN_MUTANT"] = in_fn_mutant
		env["OUT_FN"] = out_fn

		Util.RunSubp("gnuplot %s/latency-by-otts.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
