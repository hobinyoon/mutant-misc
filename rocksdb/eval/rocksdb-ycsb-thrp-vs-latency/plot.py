#!/usr/bin/env python

import multiprocessing
import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog
import RocksdbLog
import YcsbLog


def main(argv):
  Util.MkDirs(Conf.GetOutDir())
  PlotThrpLat()

  # To have a deeper understanding of what's causing the performance difference between metadata on and off.
  fn_dstat = DstatLog.GenDataThrpVsAllMetrics()


def PlotThrpLat():
  fn_ycsb = YcsbLog.GenDataThrpVsLat()

  fn_out = "%s/rocksdb-ycsb-metadata-caching-thrp-lat.pdf" % Conf.GetOutDir()

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_YCSB"] = fn_ycsb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-thrp-lat.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
