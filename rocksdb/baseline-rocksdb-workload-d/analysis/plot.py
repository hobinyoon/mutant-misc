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

  dn_log = Conf.GetDir("dn")

  #for stg_dev in ["ls", "e-gp2", "e-st1", "e-sc1"]:
  for stg_dev in ["ls"]:
    t = Conf.Get(stg_dev).split("/")
    job_id = t[0]
    exp_dt = t[1]
    #Cons.P(job_id)
    #Cons.P(exp_id)

    # TODO: Figure out the time interval to get IOPS and read/write latencies.
    #   Plot time vs cache size and see when the cache saturates. From there you can set the time range to look at.
    #   The memory usage was increasing. Because YCSB kept the raw data statistics in memory!

    # TODO: Plot (cost vs latency) by storage devices
    #
    # The goal:
    #   to show there are limited options.
    #   (or) just show the baseline.
    Plot((stg_dev, dn_log, job_id, exp_dt))

  #for line in re.split(r"\s+", exps):
  #  t = line.split("/quizup/")
  #  if len(t) != 2:
  #    raise RuntimeError("Unexpected")
  #  job_id = t[0]
  #  exp_dt = t[1]
  #  Plot((job_id, exp_dt))

  # # Parallel processing
  # params = []
  # for line in re.split(r"\s+", exps):
  #   t = line.split("/quizup/")
  #   if len(t) != 2:
  #     raise RuntimeError("Unexpected")
  #   job_id = t[0]
  #   exp_dt = t[1]
  #   params.append((job_id, exp_dt))
  # p = multiprocessing.Pool(8)
  # p.map(Plot, params)


def Plot(param):
  stg_dev = param[0]
  dn_log = param[1]
  job_id = param[2]
  exp_dt = param[3]
  dn_log_job = "%s/%s" % (dn_log, job_id)

  (fn_ycsb, time_max, params) = YcsbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  #Cons.P(time_max)

  params_formatted = pprint.pformat(params[0]) + "\n" + pprint.pformat(params[1])
  params_formatted = params_formatted.replace("_", "\\\\_").replace(" ", "\\ ").replace("\n", "\\n").replace("{", "\{").replace("}", "\}")
  #Cons.P(params_formatted)

  fn_dstat = DstatLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  fn_rocksdb = RocksdbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)

  fn_out = "%s/rocksdb-ycsb_d-%s-by-time-%s.pdf" % (Conf.GetOutDir(), stg_dev, exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["PARAMS"] = params_formatted
    env["STG_DEV"] = stg_dev
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
