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


# Automatically figuring out the time range doesn't seem to be easy. Do manually for now.
#   Start from when the file system cache gets full
#   Stop when the EBS rate limiting kicks in
#
# Performance
#   Increases during the file system cache warm-up.
#   Dips (DB IOPS dips or DB latency valleys) are caused by by SSTable flushes and compactions
#   (EBS volumes only) Drops eventually from the EBS volume rate limiting


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  exp_set_id = "171013-134330"
  #exp_set_id = "171022-160102"
  conf_exp_set = Conf.Get(exp_set_id)

  if True:
    parallel_processing = True
    if parallel_processing:
      params = []
      for stg_dev, v in conf_exp_set.iteritems():
        params.append((exp_set_id, stg_dev, v))
      p = multiprocessing.Pool()
      p.map(PlotByTime, params)
    else:
      for stg_dev, v in conf_exp_set.iteritems():
        PlotByTime((exp_set_id, stg_dev, v))

  # Plot (cost vs latency) by storage devices
  #   Latency in avg and tail latencies
  #
  # The goal:
  #   to show there are limited options
  #   and show the baseline performances.
  #
  # Finish this and show that this was not a fair comparison.
  if True:
    PlotCostLatency(exp_set_id)


def PlotByTime(params):
  exp_set_id = params[0]
  stg_dev = params[1]
  p0 = params[2]

  jobid_expdt = p0["jobid_expdt"]
  time_window = p0["time_window"]

  (fn_ycsb, time_max, params1) = YcsbLog.GenDataMetricsByTime(exp_set_id, stg_dev)
  #Cons.P(time_max)

  params_formatted = exp_set_id + "\n" + pprint.pformat(params1[0]) + "\n" + pprint.pformat(params1[1])
  params_formatted = params_formatted.replace("_", "\\\\_").replace(" ", "\\ ").replace("\n", "\\n").replace("{", "\{").replace("}", "\}")
  #Cons.P(params_formatted)

  t = jobid_expdt.split("/")
  job_id = t[0]
  exp_dt = t[1]

  dn_log = Conf.GetDir("dn")
  dn_log_job = "%s/%s" % (dn_log, job_id)

  fn_dstat = DstatLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  fn_rocksdb = RocksdbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)

  fn_out = "%s/rocksdb-ycsb_d-%s-by-time-%s.pdf" % (Conf.GetOutDir(), stg_dev, exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["EXP_SET_ID"] = exp_set_id
    env["PARAMS"] = params_formatted
    env["STG_DEV"] = stg_dev
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotCostLatency(exp_set_id):
  fn_ycsb = YcsbLog.GenDataCostVsMetrics(exp_set_id)
  fn_out = "%s/rocksdb-ycsb-cost-perf-%s.pdf" % (Conf.GetOutDir(), exp_set_id)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_YCSB"] = fn_ycsb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-cost-perf.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
