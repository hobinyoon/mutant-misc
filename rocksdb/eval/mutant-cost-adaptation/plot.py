#!/usr/bin/env python

from contextlib import contextmanager
from multiprocessing import Pool
import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import CpuAvg
import DstatLog
import ProcMemLog
import YcsbLog

sys.path.insert(0, "%s/RocksdbLog" % os.path.dirname(__file__))
import RocksdbLog


def main(argv):
  Util.MkDirs(Conf.GetOutDir())
  PlotTimeVsMetrics()

    
def PlotTimeVsMetrics():
  with Cons.MT("Plotting time vs metrics ..."):
    dn_base = Conf.GetDir("dn_base")

    params = []
    for cost_changes, v in sorted(Conf.Get("by_costchanges_targetiops").iteritems()):
      for target_iops, e in sorted(v.iteritems()):
        #Cons.P("%s %s %s" % (cost_changes, target_iops, e))
        params.append("%s/%s" % (dn_base, e))

    parallel_processing = False
    if parallel_processing:
      with terminating(Pool()) as pool:
        pool.map(_PlotTimeVsAllMetrics, params)
    else:
      for p in params:
        _PlotTimeVsAllMetrics(p)


def _PlotTimeVsAllMetrics(fn_ycsb_log):
  # 171121-194901/ycsb/171122-010708.903-d
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)

  fn_out = "%s/time-vs-all-metrics-%s.pdf" % (Conf.GetOutDir(), exp_dt)
  if os.path.exists(fn_out):
    Cons.P("%s %d already exists." % (fn_out, os.path.getsize(fn_out)))
    return

  (fn_ycsb, time_max, params1) = YcsbLog.GenDataMetricsByTime(fn_ycsb_log, exp_dt)
  #Cons.P("%s\n%s\n%s" % (fn_ycsb, time_max, params1))
  #time_max = "00:30:00"

  params_formatted = fn_ycsb_log + "\n" + pprint.pformat(params1[0]) + "\n" + pprint.pformat(params1[1])
  # No idea how to put spaces for the indentations. It used to work.
  #   Neither replace(" ", "\ ") or replace(" ", "\\ ") worked when a line starts with spaces followed by digits or [.
  #     work when it is followed by u. I guess regular characters.
  params_formatted = params_formatted.replace("_", "\\\\_").replace("\n", "\\n").replace("{", "\{").replace("}", "\}")
  #Cons.P(params_formatted)

  dn_log_job = "%s/%s" % (dn_log, job_id)

  (fn_dstat, num_stgdevs) = DstatLog.GetPlotFn1(dn_log_job, exp_dt)
  (fn_rocksdb, target_cost_changes) = RocksdbLog.GetFnTimeVsMetrics(fn_ycsb_log)
  #Cons.P(target_cost_changes)

  fn_cpu_avg = CpuAvg.GetFnForPlot(fn_ycsb_log)
  fn_mem_usage = ProcMemLog.GetFnForPlot(dn_log, job_id, exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["PARAMS"] = params_formatted
    env["NUM_STGDEVS"] = str(num_stgdevs)
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["IN_FN_CPU_AVG"] = fn_cpu_avg
    env["IN_FN_MEM"] = fn_mem_usage
    env["TARGET_COST_CHANGES_TIME"] = target_cost_changes[0]
    env["TARGET_COST_CHANGES_COST"] = target_cost_changes[1]
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/time-vs-all-metrics.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  sys.exit(0)


class ExpTuple:
  def __init__(self, o_cpu, o_mem, p):
    self.o_cpu = o_cpu
    self.o_mem = o_mem
    self.fn_rocksdb = p[0]
    self.fn_computation = p[1]

  def __lt__(self, other):
    if self.o_cpu < other.o_cpu:
      return True
    elif self.o_cpu > other.o_cpu:
      return False
    if self.o_mem < other.o_mem:
      return True
    elif self.o_mem > other.o_mem:
      return False
    if self.fn_rocksdb < other.fn_rocksdb:
      return True
    elif self.fn_rocksdb > other.fn_rocksdb:
      return False
    return (self.fn_computation < other.fn_computation)

  def GetExpDt(self, which):
    if which == "r":
      fn = self.fn_rocksdb
    elif which == "c":
      fn = self.fn_computation
    else:
      raise RuntimeError("Unexpected")

    pattern = r".+/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)-d"
    mo = re.match(pattern, fn)
    return mo.group("exp_dt")


@contextmanager
def terminating(thing):
  try:
    yield thing
  finally:
    thing.terminate()


if __name__ == "__main__":
  sys.exit(main(sys.argv))
