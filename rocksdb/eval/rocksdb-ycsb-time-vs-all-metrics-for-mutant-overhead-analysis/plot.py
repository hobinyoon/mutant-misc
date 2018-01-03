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

  # Experiment root
  dn_base = Conf.GetDir("dn_base")

  params = []
  fn = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
  params.append((fn, ))

  parallel_processing = False
  if parallel_processing:
    p = multiprocessing.Pool()
    p.map(PlotByTime, params)
  else:
    for p in params:
      PlotByTime(p)


def PlotByTime(params):
  fn_ycsb_log = params[0]

  # 171121-194901/ycsb/171122-010708.903-d
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)

  (fn_ycsb, time_max, params1) = YcsbLog.GenDataMetricsByTime(fn_ycsb_log, exp_dt)
  #Cons.P("%s\n%s\n%s\n%s" % (fn_ycsb, time_max, params1[0], params1[1]))
  # For dev
  #time_max = "00:10:00"
  #time_max = "03:00:00"

  params_formatted = fn_ycsb_log + "\n" + pprint.pformat(params1[0]) + "\n" + pprint.pformat(params1[1])
  # The last, space substitution doesn't seem to work all of a sudden. Not the highest priority.
  params_formatted = params_formatted.replace("\n", "\\n").replace("_", "\\\\_").replace("{", "\{").replace("}", "\}") #.replace(" ", "\\ ")
  #Cons.P(params_formatted)

  dn_log_job = "%s/%s" % (dn_log, job_id)

  (fn_dstat, num_stgdevs) = DstatLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  #Cons.P("%s %s" % (fn_dstat, num_stgdevs))
  fn_rocksdb = RocksdbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)

  fn_out = "%s/rocksdb-ycsb-all-metrics-by-time-%s.pdf" % (Conf.GetOutDir(), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["PARAMS"] = params_formatted
    env["NUM_STG_DEVS"] = str(num_stgdevs)
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-all-metrics-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
