#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import YcsbLog


# Performance
#   Increases during the file system cache warm-up.
#   Dips (DB IOPS dips or DB latency valleys) are caused by by SSTable flushes and compactions
#   (EBS volumes only) Drops eventually from the EBS volume rate limiting


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  PlotThrpLat()


def PlotThrpLat():
  fn_ycsb = YcsbLog.GenDataThrpVsLat()
  fn_out = "%s/mutant-ycsb-thrp-vs-lat-by-costslos.pdf" % Conf.GetOutDir()

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_YCSB"] = fn_ycsb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/mutant-ycsb-thrp-lat.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
