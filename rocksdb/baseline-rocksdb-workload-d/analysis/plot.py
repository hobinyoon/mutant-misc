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
  stg_devs = ["ls", "e-gp2", "e-st1", "e-sc1"]
  #stg_devs = ["ls"]

  parallel_processing = True
  if parallel_processing:
    params = []
    for stg_dev in stg_devs:
      params.append(stg_dev)
    p = multiprocessing.Pool()
    p.map(PlotByTime, params)
  else:
    for stg_dev in stg_devs:
      PlotByTime(stg_dev)

  # TODO: Plot (cost vs latency) by storage devices
  #   Latency in avg and tail latencies
  #
  # The goal:
  #   to show there are limited options
  #   and show the baseline performances.
  PlotCostLatency(stg_devs)


def PlotByTime(stg_dev):
  conf_sd = Conf.Get(stg_dev)

  t = conf_sd["jobid_expdt"].split("/")
  job_id = t[0]
  exp_dt = t[1]

  t = conf_sd["time_window"].split("-")
  exp_time_begin = t[0]
  exp_time_end   = t[1]

  dn_log = Conf.GetDir("dn")
  dn_log_job = "%s/%s" % (dn_log, job_id)

  (fn_ycsb, time_max, params) = YcsbLog.GenDataFileForGnuplot(dn_log_job, exp_dt, exp_time_begin, exp_time_end)
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


def PlotCostLatency(stg_devs):
  # TODO: Parse the comment section of the output files
  # Reuse this one
  # (fn_ycsb, time_max, params) = YcsbLog.GenDataFileForGnuplot(dn_log_job, exp_dt, exp_time_begin, exp_time_end)






if __name__ == "__main__":
  sys.exit(main(sys.argv))
