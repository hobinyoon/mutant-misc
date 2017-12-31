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
  #r = Conf.Get("rocksdb-metadata-org")
  r = Conf.Get("rocksdb-baseline")

  dn_base = r["dn_base"].replace("~", os.path.expanduser("~"))

  params = []
  #for stgdev in ["ebs-st1", "local-ssd"]:
  for stgdev in ["local-ssd"]:
    for target_iops, jobid_expdt in r[stgdev].iteritems():
      fn_in = "%s/%s" % (dn_base, jobid_expdt)
      params.append((fn_in, stgdev))

  parallel_processing = True
  if parallel_processing:
    p = multiprocessing.Pool()
    p.map(PlotByTime, params)
  else:
    for p in params:
      PlotByTime(p)


def PlotByTime(params):
  fn_ycsb_log = params[0]
  stgdev = params[1]

  # 171121-194901/ycsb/171122-010708.903-d
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)

  (fn_ycsb, time_max, params1) = YcsbLog.GenDataMetricsByTime(fn_ycsb_log, exp_dt)
  #Cons.P("%s\n%s\n%s" % (fn_ycsb, time_max, params1))

  params_formatted = fn_ycsb_log + "\n" + pprint.pformat(params1[0]) + "\n" + pprint.pformat(params1[1])
  params_formatted = params_formatted.replace("_", "\\\\_").replace(" ", "\\ ").replace("\n", "\\n").replace("{", "\{").replace("}", "\}")
  #Cons.P(params_formatted)

  dn_log_job = "%s/%s" % (dn_log, job_id)

  fn_dstat = DstatLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  fn_rocksdb = RocksdbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)

  fn_out = "%s/rocksdb-ycsb-all-metrics-by-time-%s.pdf" % (Conf.GetOutDir(), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["PARAMS"] = params_formatted
    env["STG_DEV"] = stgdev
    env["TIME_MAX"] = str(time_max)
    env["IN_FN_DSTAT"] = fn_dstat
    env["IN_FN_YCSB"] = fn_ycsb
    env["IN_FN_ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/rocksdb-ycsb-all-metrics-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
