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
import ProcMemLog

sys.path.insert(0, "%s/RocksdbLog" % os.path.dirname(__file__))
import RocksdbLog

import Stat
import YcsbLog


def main(argv):
  Util.MkDirs(Conf.GetOutDir())

  PlotOverheadByTime()

    
def PlotOverheadByTime():
  (fn_rocksdb0, fn_rocksdb1, fn_rocksdb_compmigr_histo) = RocksdbLog.GenDataFilesForGnuplot()
  fn_cpu_stat_by_time = _GetFnCpuOverhead()
  fn_mem_stat_by_time = _GetFnMemOverhead()
  #time_max = "09:00:00"
  time_max = "08:00:00"
  fn_out = "%s/mutant-overhead.pdf" % Conf.GetOutDir()

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["TIME_MAX"] = str(time_max)
    env["CPU_STAT"] = fn_cpu_stat_by_time
    env["MEM_STAT"] = fn_mem_stat_by_time
    env["ROCKSDB0"] = fn_rocksdb0
    env["ROCKSDB1"] = fn_rocksdb1
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/mutant-overhead-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


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
    fmt = "%2d" \
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

  col_time = 17

  col_cpu_idle = 19
  col_cpu_sys  = col_cpu_idle + 2
  col_cpu_user = col_cpu_idle + 3
  col_cpu_iowait = col_cpu_idle + 4
  # With SSTable organization computation, there is less CPU usage and a bit more iowait time.
  #   Puzzling. Can't explain why the CPU usage is lower when SSTable organization computation is on
  #   The slightly increased iowait time towards the end might be from the increased amount of log and the overhead of zipping and uploading them.
  which_cpu = "overall"
  #which_cpu = "user"
  #which_cpu = "user+kernel"
  #which_cpu = "iowait"

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

      if which_cpu == "overall":
        cpu = 100.0 - float(t[col_cpu_idle - 1])
      elif which_cpu == "user":
        cpu = float(t[col_cpu_user - 1])
      elif which_cpu == "user+kernel":
        cpu = float(t[col_cpu_user - 1]) + float(t[col_cpu_sys - 1])
      elif which_cpu == "iowait":
        cpu = float(t[col_cpu_iowait - 1])
      else:
        raise RuntimeError("Unexpected")

      #Cons.P("%s %s" % (time0, cpu))
      hour = int(time0.split(":")[0])
      if hour not in hour_cpuusage:
        hour_cpuusage[hour] = []
      hour_cpuusage[hour].append(cpu)

  hour_cpustat = {}
  for hour, cpu_usage in hour_cpuusage.iteritems():
    r = Stat.Gen(cpu_usage)
    #Cons.P("%d %s" % (hour, r))
    hour_cpustat[hour] = r
  return hour_cpustat


def _GetFnMemOverhead():
  fn_out = "%s/memory-overhead-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating file for memory overhead plotting ..."):
    dn_base = Conf.GetDir("dn_base")
    fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
    fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get("computation_overhead"))

    hour_memstat_0 = _GetMemStatByHour(fn_ycsb_0)
    hour_memstat_1 = _GetMemStatByHour(fn_ycsb_1)
    #Cons.P(hour_memstat_0)
    #Cons.P(hour_memstat_1)

    with open(fn_out, "w") as fo:
      fo.write("# u: unmodified\n")
      fo.write("# c: with SSTable access monitoring and SSTable placement computation\n")
      fo.write("#\n")
      fmt = "%2d" \
          " %10d %10d %10d %10d %10d %10d %10d %10d" \
          " %10d %10d %10d %10d %10d %10d %10d %10d"
      fo.write(Util.BuildHeader(fmt, "hour" \
          " u_avg u_min u_1 u_25 u_50 u_75 u_99 u_max" \
          " c_avg c_min c_1 c_25 c_50 c_75 c_99 c_max"
          ) + "\n")
      for h, s0 in sorted(hour_memstat_0.iteritems()):
        s1 = hour_memstat_1[h]
        fo.write((fmt + "\n") % (h
          , s0.avg, s0.min, s0._1, s0._25, s0._50, s0._75, s0._99, s0.max
          , s1.avg, s1.min, s1._1, s1._25, s1._50, s1._75, s1._99, s1.max
          ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


def _GetMemStatByHour(fn_ycsb):
  #return _GetMemStatByHourFromDstat(fn_ycsb)
  return _GetMemStatByHourFromProc(fn_ycsb)


def _GetMemStatByHourFromDstat(fn_ycsb):
  fn_dstat = _GenDstat(fn_ycsb)

  col_time = 21
  col_mem_buff = 13
  #col_mem_cache = 14

  #Cons.P(fn_dstat)
  # Bucketize CPU usage
  #   {hour: [mem_usage]}
  hour_memusage = {}
  with open(fn_dstat) as fo:
    for line in fo:
      if line.startswith("#"):
        continue
      line = line.strip()
      t = re.split(r" +", line)
      time0 = t[col_time - 1]
      mem_buff = int(t[col_mem_buff - 1])
      #Cons.P("%s %d" % (time0, mem_buff))
      hour = int(time0.split(":")[0])
      if hour not in hour_memusage:
        hour_memusage[hour] = []
      hour_memusage[hour].append(mem_buff)

  hour_memstat = {}
  for hour, mem_usage in hour_memusage.iteritems():
    r = Stat.Gen(mem_usage)
    #Cons.P("%d %s" % (hour, r))
    hour_memstat[hour] = r
  return hour_memstat


def _GetMemStatByHourFromProc(fn_ycsb):
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")

  dn_log_job = "%s/%s" % (dn_log, job_id)
  return ProcMemLog.GenMemStatByHour(dn_log_job, exp_dt)


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
