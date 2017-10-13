#!/usr/bin/env python

import datetime
import math
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
from QuizupLog import QuizupLog
import RocksdbLog
import SimTime


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  dn_log = Conf.GetDir("dn")

  stg_dev = "ls"
  t = Conf.Get(stg_dev).split("/")
  job_id = t[0]
  exp_dt = t[1]
  #Cons.P(job_id)
  #Cons.P(exp_id)

  # TODO: Figure out the time interval to get IOPS and read/write latencies.
  #   Plot time vs cache size and see when the cache saturates. From there you can set the time range to look at.
  #   The memory usage was increasing. Because YCSB kept the raw data statistics in memory!

  # TODO: Plot time vs perf metrics
  # TODO: Plot (cost vs latency) by storage devices
  #
  # The goal:
  #   to show there are limited options.
  #   (or) just show the baseline.
  Plot((stg_dev, dn_log, job_id, exp_dt))
  sys.exit(0)
  
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

  fn_log_dstat = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)
  fn_dstat = DstatLog.GenDataFileForGnuplot(fn_log_dstat, exp_dt)

  fn_out = "%s/rocksdb-ycsb_d-%s-by-time-%s.pdf" % (Conf.GetOutDir(), stg_dev, exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_FN_DSTAT"] = fn_dstat
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  sys.exit(0)

  fn_log_quizup  = "%s/quizup/%s" % (dn_log_job, exp_dt)
  fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)


  log_q = QuizupLog(fn_log_quizup)
  SimTime.Init(log_q.SimTime("simulated_time_begin"), log_q.SimTime("simulated_time_end")
      , log_q.SimTime("simulation_time_begin"), log_q.SimTime("simulation_time_end"))

  qz_std_max = _QzSimTimeDur(log_q.quizup_options["simulation_time_dur_in_sec"])
  qz_opt_str = _QuizupOptionsFormattedStr(log_q.quizup_options)
  error_adj_ranges = log_q.quizup_options["error_adj_ranges"].replace(",", " ")

  (fn_rocksdb_sla_admin_log, pid_params, num_sla_adj) = RocksdbLog.ParseLog(fn_log_rocksdb, exp_dt)


  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["STD_MAX"] = qz_std_max
    env["ERROR_ADJ_RANGES"] = error_adj_ranges
    env["IN_FN_QZ"] = fn_log_quizup
    env["IN_FN_SLA_ADMIN"] = "" if num_sla_adj == 0 else fn_rocksdb_sla_admin_log
    env["QUIZUP_OPTIONS"] = qz_opt_str
    env["PID_PARAMS"] = "%s %s %s %s" % (pid_params["target_value"], pid_params["p"], pid_params["i"], pid_params["d"])
    env["WORKLOAD_EVENTS"] = " ".join(str(t) for t in log_q.simulation_time_events)
    env["IN_FN_DS"] = fn_dstat
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/sla-admin-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# List the options in 2 columns, column first.
def _QuizupOptionsFormattedStr(quizup_options):
  max_width = 0
  i = 0
  num_rows = int(math.ceil(len(quizup_options) / 2.0))
  for k, v in sorted(quizup_options.iteritems()):
    max_width = max(max_width, len("%s: %s" % (k, v)))
    i += 1
    if i == num_rows:
      break

  strs = []
  fmt = "%%-%ds" % (max_width + 1)
  for k, v in sorted(quizup_options.iteritems()):
    strs.append(fmt % ("%s: %s" % (k, v)))
  #Cons.P("\n".join(strs))
  for i in range(num_rows):
    if i + num_rows < len(strs):
      strs[i] += strs[i + num_rows]
  strs = strs[:num_rows]
  #Cons.P("\n".join(strs))
  qz_opt_str = "\\n".join(strs).replace("_", "\\\\_").replace(" ", "\\ ")
  #Cons.P(qz_opt_str)
  return qz_opt_str


# Simulation time duration
def _QzSimTimeDur(std):
  s = int(std)
  std_s = s % 60
  std_m = int(s / 60) % 60
  std_h = int(s / 3600)
  return "%02d:%02d:%02d" % (std_h, std_m, std_s)


if __name__ == "__main__":
  sys.exit(main(sys.argv))
