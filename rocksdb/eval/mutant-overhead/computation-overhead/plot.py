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

sys.path.insert(0, "%s/CompareTwo" % os.path.dirname(__file__))
import CompareCpu
import CompareMem


def main(argv):
  Util.MkDirs(Conf.GetOutDir())
  PlotTimeVsMetrics()
  exp_tuples = CalcCompareTwo()
  PlotCompareTwo(exp_tuples)

    
def PlotTimeVsMetrics():
  with Cons.MT("Plotting time vs metrics ..."):
    dn_base = Conf.GetDir("dn_base")
    exps_rocksdb = Conf.Get("rocksdb")
    exps_computation = Conf.Get("computation")
    #Cons.P(pprint.pformat(exps_rocksdb))
    #Cons.P(pprint.pformat(exps_computation))

    params = []
    for e in exps_rocksdb:
      params.append("%s/%s" % (dn_base, e))
    for e in exps_computation:
      params.append("%s/%s" % (dn_base, e))

    parallel_processing = True
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
  fn_rocksdb = RocksdbLog.GetFnTimeVsMetrics(fn_ycsb_log)

  fn_cpu_avg = CpuAvg.GetFnForPlot(fn_ycsb_log)
  fn_mem_usage = ProcMemLog.GetFnForPlot(dn_log, job_id, exp_dt)

  # Don't need the actual plot for now. Plus, plotting takes too much time.
  return

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
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/time-vs-all-metrics.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def CalcCompareTwo():
  with Cons.MT("Calculating the overhead of pairs ..."):
    dn_base = Conf.GetDir("dn_base")
    exps_rocksdb = Conf.Get("rocksdb")
    exps_computation = Conf.Get("computation")

    params = []
    for r in exps_rocksdb:
      for c in exps_computation:
        params.append(("%s/%s" % (dn_base, r), "%s/%s" % (dn_base, c)))

    parallel_processing = True
    if parallel_processing:
      with terminating(Pool()) as pool:
        pool.map(_CalcCompareTwo, params)
    else:
      for p in params:
        _CalcCompareTwo(p)

    # Find the closest pair
    #   You want the computation overhead one has the minimal overhead, but no smaller than the rocksdb one.
    exp_tuples = []
    for p in params:
      o_cpu = CompareCpu.GetOverhead(p[0], p[1])
      o_mem = CompareMem.GetOverhead(p[0], p[1])
      if (o_cpu < 1.0) or (o_mem < 1.0):
        continue
      exp_tuples.append(ExpTuple(o_cpu, o_mem, p))

    fmt = "%8.6f %8.6f %17s %17s"
    Cons.P(Util.BuildHeader(fmt, "cpu_overhead mem_overhead expdt_rocksdb expdt_computation"))

    for e in sorted(exp_tuples):
      Cons.P(fmt % (
        e.o_cpu
        , e.o_mem
        , e.GetExpDt("r")
        , e.GetExpDt("c")
        ))
    return exp_tuples


def PlotCompareTwo(exp_tuples):
  with Cons.MT("Plotting compare two exps ..."):
    params = []
    for e in exp_tuples:
      params.append((e.fn_rocksdb, e.fn_computation))

    parallel_processing = True
    if parallel_processing:
      with terminating(Pool()) as pool:
        pool.map(_PlotCompareTwo, params)
    else:
      for p in params:
        _PlotCompareTwo(p)


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


def _CalcCompareTwo(params):
  exp_rocksdb = params[0]
  exp_computation = params[1]
  fn_cpu_1min_avg = CompareCpu.Get1minAvgFn(exp_rocksdb, exp_computation)
  fn_mem_1min_avg = CompareMem.Get1minAvgFn(exp_rocksdb, exp_computation)


def _PlotCompareTwo(params):
  exp_rocksdb = params[0]
  exp_computation = params[1]

  exp_dts = []
  pattern = r".+/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)-d"
  mo = re.match(pattern, exp_rocksdb)
  exp_dts.append(mo.group("exp_dt"))
  mo = re.match(pattern, exp_computation)
  exp_dts.append(mo.group("exp_dt"))
  fn_out = "%s/mutant-computation-overhead-%s.pdf" % (Conf.GetOutDir(), "-".join(exp_dts))
  if os.path.exists(fn_out):
    #Cons.P("%s %d already exists" % (fn_out, os.path.getsize(fn_out)))
    return

  plot_custom_labels = ("-".join(exp_dts) == "180201-033312.464-180201-033259.439")

  fn_rocksdb = RocksdbLog.GetFnTimeVsMetrics(exp_rocksdb)

  time_max = "07:50:00"
  fn_cpu_1min_avg = CompareCpu.Get1minAvgFn(exp_rocksdb, exp_computation)
  fn_mem_1min_avg = CompareMem.Get1minAvgFn(exp_rocksdb, exp_computation)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["TIME_MAX"] = str(time_max)
    env["FN_ROCKSDB"] = fn_rocksdb
    env["FN_CPU_1MIN_AVG"] = fn_cpu_1min_avg
    env["FN_MEM_1MIN_AVG"] = fn_mem_1min_avg
    env["PLOT_CUSTOM_LABELS"] = "1" if plot_custom_labels else "0"
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/compare-two-exps.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


@contextmanager
def terminating(thing):
  try:
    yield thing
  finally:
    thing.terminate()


if __name__ == "__main__":
  sys.exit(main(sys.argv))
