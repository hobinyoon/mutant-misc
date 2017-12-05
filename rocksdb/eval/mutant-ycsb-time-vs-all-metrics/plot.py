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


# Plot time vs. all metrics to
#   figure out the experiment time range.
#     Start when the file system cache gets full and the DB IOPS gets stabilized
#     Stop when the DB IOPS drops, such as from the EBS rate limiting.
#   to see if everything went as expected.
#     Dips (DB IOPS dips or DB latency valleys)
#       caused from SSTable flushes and compactions
#       for seemingly no reason. Probably from the shared cloud environment.


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  # Experiment root
  r = Conf.Get("cost-vs-perf")

  dn_base = r["dn_base"].replace("~", os.path.expanduser("~"))

  params = []
  for cost_slo_str, v in r["exps"].iteritems():
    t = cost_slo_str.split(", ")
    cost_slo = float(t[0])
    cost_slo_epsilon = float(t[1])
    #Cons.P("%f %f" % (cost_slo, cost_slo_epsilon))

    for target_iops, fn in v.iteritems():
      #Cons.P("  %s %s" % (target_iops, fn))
      # 171204-162903/ycsb/171204-214803.510-d
      mo = re.match(r"(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)-(?P<workload>\w)", fn)
      job_id = mo.group("job_id")
      exp_dt = mo.group("exp_dt")
      workload = mo.group("workload")
      #Cons.P((job_id, exp_dt, workload))
      params.append(ExpParam(dn_base, target_iops, cost_slo, cost_slo_epsilon, job_id, exp_dt, workload))
  #Cons.P(pprint.pformat(params))

  parallel_processing = True
  if parallel_processing:
    p = multiprocessing.Pool()
    p.map(PlotByTime, params)
  else:
    for p in params:
      PlotByTime(p)


class ExpParam:
  def __init__(self, dn_base, target_iops, cost_slo, cost_slo_epsilon, job_id, exp_dt, workload):
    self.dn_base          = dn_base
    self.target_iops      = target_iops
    self.cost_slo         = cost_slo
    self.cost_slo_epsilon = cost_slo_epsilon
    self.job_id           = job_id
    self.exp_dt           = exp_dt
    self.workload         = workload
  def __repr__(self):
    return pprint.pformat(vars(self))


def PlotByTime(p):
  (fn_ycsb, time_max, params1) = YcsbLog.GenDataMetricsByTime(p)
  #Cons.P("%s\n%s\n%s" % (fn_ycsb, time_max, params1))

  params_formatted = str(p).replace("_", "\\\\_").replace(" ", "\\ ").replace("\n", "\\n").replace("{", "\{").replace("}", "\}")
  #Cons.P(params_formatted)

  fn_dstat = DstatLog.GenDataFileForGnuplot(p)
  fn_rocksdb = RocksdbLog.GenDataFileForGnuplot(p)

  fn_out = "%s/rocksdb-ycsb-all-metrics-by-time-%s.pdf" % (Conf.GetOutDir(), p.exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["PARAMS"] = params_formatted
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-all-metrics-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
