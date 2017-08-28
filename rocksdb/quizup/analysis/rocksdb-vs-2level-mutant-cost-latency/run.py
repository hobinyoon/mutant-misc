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

	PlotRocksDbMutantCostLatency()


def PlotRocksDbMutantCostLatency():
	in_fn_rocksdb = LogReader.GetRocksDbCostLatencyDataFile()
	in_fn_mutant = LogReader.GetMutantCostLatencyDataFile()
	out_fn = "%s/.output/rocksdb-2level-mutant-cost-latency.pdf" % os.path.dirname(__file__)
	out_fn1 = "%s/.output/rocksdb-2level-mutant-cost-latency-1.pdf" % os.path.dirname(__file__)
	out_fn2 = "%s/.output/rocksdb-2level-mutant-cost-latency-2.pdf" % os.path.dirname(__file__)
	out_fn3 = "%s/.output/rocksdb-2level-mutant-cost-latency-3.pdf" % os.path.dirname(__file__)
	out_fn4 = "%s/.output/rocksdb-2level-mutant-cost-latency-4.pdf" % os.path.dirname(__file__)

	env = os.environ.copy()
	env["IN_FN_ROCKSDB"] = in_fn_rocksdb
	env["IN_FN_MUTANT"] = in_fn_mutant
	env["OUT_FN"] = out_fn
	env["OUT_FN1"] = out_fn1
	env["OUT_FN2"] = out_fn2
	env["OUT_FN3"] = out_fn3
	env["OUT_FN4"] = out_fn4

	Util.RunSubp("gnuplot %s/cost-latency.gnuplot" % os.path.dirname(__file__), env=env)
	Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
