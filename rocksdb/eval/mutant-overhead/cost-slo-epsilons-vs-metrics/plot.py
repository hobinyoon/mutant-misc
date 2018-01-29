#!/usr/bin/env python

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

# (# of the total size) of SSTables that are
#   compacted
#     compaction-migrated (show the efficacy of the integration)
#   migrated
#
#   How well does Mutant meet the target cost SLOs

def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  # TODO: Cost SLO epsilon vs. the number of the total amount of SSTables migrated.
  exps = []
  # TODO:
  #Conf.Get("unmodified_db")

  RocksdbLog.GetFnCostSloEpsilonVsNumCompMigrs()




  # TODO: clean up
  #PlotTimeVsAllMetrics()
  #PlotCompareTwo()

    
def PlotTimeVsAllMetrics():
  dn_base = Conf.GetDir("dn_base")
  for i in range(2):
    fn_ycsb = "%s/%s" % (dn_base, Conf.Get(i))
    _PlotTimeVsAllMetrics(fn_ycsb)


# Not parallizable cause DstatLog is not. Not checked with RocksdbLog.
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

  (fn_dstat, num_stgdevs)  = DstatLog.GetPlotFn1(dn_log_job, exp_dt)
  fn_rocksdb = RocksdbLog.GetFnTimeVsMetrics(fn_ycsb_log)

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
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/time-vs-all-metrics.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotCompareTwo():
  (fns_rocksdb, fn_sst_creation_stat) = RocksdbLog.GenDataFilesForGnuplot()
  #fn_cpu_stat_by_time = CompareCpu.GetHourlyFn()
  fn_cpu_1min_avg = CompareCpu.Get1minAvgFn()
  fn_mem_stat_by_time = CompareMem.GetHourlyFn()
  fn_mem_1min_avg = CompareMem.Get1minAvgFn()
  #time_max = "09:00:00"
  #time_max = "08:00:00"
  time_max = "07:50:00"

  exp_dts = []
  for i in range(2):
    mo = re.match(r".+/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)-d", Conf.Get(i))
    exp_dts.append(mo.group("exp_dt"))
  fn_out = "%s/mutant-overhead-%s.pdf" % (Conf.GetOutDir(), "-".join(exp_dts))

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["TIME_MAX"] = str(time_max)
    #env["CPU_STAT"] = fn_cpu_stat_by_time
    env["FN_CPU_1MIN_AVG"] = fn_cpu_1min_avg
    #env["MEM_STAT"] = fn_mem_stat_by_time
    env["FN_MEM_1MIN_AVG"] = fn_mem_1min_avg
    env["ROCKSDB0"] = fns_rocksdb[0]
    env["ROCKSDB1"] = fns_rocksdb[1]
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/compare-two-exps.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
