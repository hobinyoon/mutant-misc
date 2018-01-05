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
import Stat
import YcsbLog


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  PlotCpuOverheadByTime()

    
def PlotCpuOverheadByTime():
  fn_cpu_stat_by_time = _GetFnCpuOverhead()
  fn_rocksdb = _GetFnRocksDB()
  time_max = "09:00:00"
  fn_out = "%s/mutant-overhead.pdf" % Conf.GetOutDir()

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["TIME_MAX"] = str(time_max)
    env["CPU_STAT"] = fn_cpu_stat_by_time
    env["ROCKSDB"] = fn_rocksdb
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/mutant-overhead-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


  sys.exit(0)

  fn_ycsb_log = params[0]

  # 171121-194901/ycsb/171122-010708.903-d
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)


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


def _GetFnRocksDB():
  dn_base = Conf.GetDir("dn_base")
  fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_0)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)

  dn_log_job = "%s/%s" % (dn_log, job_id)
  return RocksdbLog.GenDataFileForGnuplot(dn_log_job, exp_dt)


def _GetFnCpuOverhead():
  fn_out = "%s/cpu-overhead-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  dn_base = Conf.GetDir("dn_base")
  fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
  fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get("computation_overhead"))

  hour_cpustat_0 = _GetCpuStatByHour(fn_ycsb_0)
  hour_cpustat_1 = _GetCpuStatByHour(fn_ycsb_1)
  #Cons.P(hour_cpustat_0)
  #Cons.P(hour_cpustat_1)

  with open(fn_out, "w") as fo:
    fo.write("# u: unmodified\n")
    fo.write("# c: with SSTable access monitoring and SSTable placement computation\n")
    fo.write("#\n")
    fmt = "%1d" \
        " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f" \
        " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f"
    fo.write(Util.BuildHeader(fmt, "hour" \
        " u_avg u_min u_1 u_25 u_50 u_75 u_99 u_max" \
        " c_avg c_min c_1 c_25 c_50 c_75 c_99 c_max"
        ) + "\n")
    for h, s0 in sorted(hour_cpustat_0.iteritems()):
      s1 = hour_cpustat_1[h]
      fo.write((fmt + "\n") % (h
        , s0.avg, s0.min, s0._1, s0._25, s0._50, s0._75, s0._99, s0.max
        , s1.avg, s1.min, s1._1, s1._25, s1._50, s1._75, s1._99, s1.max
        ))
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


def _GetCpuStatByHour(fn_ycsb):
  fn_dstat = _GenDstat(fn_ycsb)

  col_time = 21
  col_cpu_idle = 23

  #Cons.P(fn_dstat)
  # Bucketize CPU usage
  #   {hour: [cpu_usage]}
  hour_cpuusage = {}
  with open(fn_dstat) as fo:
    for line in fo:
      if line.startswith("#"):
        continue
      line = line.strip()
      t = re.split(r" +", line)
      time0 = t[col_time - 1]
      cpu_idle = float(t[col_cpu_idle - 1])
      #Cons.P("%s %s" % (time0, cpu_idle))
      hour = int(time0.split(":")[0])
      if hour not in hour_cpuusage:
        hour_cpuusage[hour] = []
      hour_cpuusage[hour].append(100.0 - cpu_idle)

  hour_cpustat = {}
  for hour, cpu_usage in hour_cpuusage.iteritems():
    r = Stat.Gen(cpu_usage)
    #Cons.P("%d %s" % (hour, r))
    hour_cpustat[hour] = r
  return hour_cpustat


def _GenDstat(fn_ycsb_log):
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")

  dn_log_job = "%s/%s" % (dn_log, job_id)
  (fn_dstat, num_stgdevs) = DstatLog.GenDataFileForGnuplot(dn_log_job, exp_dt)
  return fn_dstat


if __name__ == "__main__":
  sys.exit(main(sys.argv))
