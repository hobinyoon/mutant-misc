import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog
import ProcMemLog
import Stat

def GetFn():
  fn_out = "%s/memory-usage-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating file for memory usage comparison ..."):
    dn_base = Conf.GetDir("dn_base")
    fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get(0))
    fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get(1))

    hour_memstat_0 = _GetMemStatByHour(fn_ycsb_0)
    hour_memstat_1 = _GetMemStatByHour(fn_ycsb_1)
    #Cons.P(hour_memstat_0)
    #Cons.P(hour_memstat_1)

    with open(fn_out, "w") as fo:
      fo.write("# 0: %s\n" % fn_ycsb_0)
      fo.write("# 1: %s\n" % fn_ycsb_1)
      fo.write("#\n")
      fmt = "%2d" \
          " %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f" \
          " %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f"
      fo.write(Util.BuildHeader(fmt, "hour" \
          " 0_avg 0_min 0_1 0_25 0_50 0_75 0_99 0_max" \
          " 1_avg 1_min 1_1 1_25 1_50 1_75 1_99 1_max"
          ) + "\n")
      for h, s0 in sorted(hour_memstat_0.iteritems()):
        s1 = hour_memstat_1[h]
        fo.write((fmt + "\n") % (h
          , (float(s0.avg) / 1024 / 1024 / 1024)
          , (float(s0.min) / 1024 / 1024 / 1024)
          , (float(s0._1 ) / 1024 / 1024 / 1024)
          , (float(s0._25) / 1024 / 1024 / 1024)
          , (float(s0._50) / 1024 / 1024 / 1024)
          , (float(s0._75) / 1024 / 1024 / 1024)
          , (float(s0._99) / 1024 / 1024 / 1024)
          , (float(s0.max) / 1024 / 1024 / 1024)

          , (float(s1.avg) / 1024 / 1024 / 1024)
          , (float(s1.min) / 1024 / 1024 / 1024)
          , (float(s1._1 ) / 1024 / 1024 / 1024)
          , (float(s1._25) / 1024 / 1024 / 1024)
          , (float(s1._50) / 1024 / 1024 / 1024)
          , (float(s1._75) / 1024 / 1024 / 1024)
          , (float(s1._99) / 1024 / 1024 / 1024)
          , (float(s1.max) / 1024 / 1024 / 1024)
          ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


def _GetMemStatByHour(fn_ycsb):
  #return _GetMemStatByHourFromDstat(fn_ycsb)
  return _GetMemStatByHourFromProc(fn_ycsb)


def _GetMemStatByHourFromDstat(fn_ycsb):
  fn_dstat = DstatLog.GetPlotFn(fn_ycsb)

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
