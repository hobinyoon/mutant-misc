import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog
import Stat

def GetFn():
  fn_out = "%s/cpu-usage-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating file for cpu usage comparison ..."):
    dn_base = Conf.GetDir("dn_base")
    fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get(0))
    fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get(1))

    hour_cpustat_0 = _GetCpuStatByHour(fn_ycsb_0)
    hour_cpustat_1 = _GetCpuStatByHour(fn_ycsb_1)
    #Cons.P(hour_cpustat_0)
    #Cons.P(hour_cpustat_1)

    with open(fn_out, "w") as fo:
      fo.write("# 0: %s\n" % fn_ycsb_0)
      fo.write("# 1: %s\n" % fn_ycsb_1)
      fo.write("#\n")
      fmt = "%2d" \
          " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f" \
          " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f"
      fo.write(Util.BuildHeader(fmt, "hour" \
          " 0_avg 0_min 0_1 0_25 0_50 0_75 0_99 0_max" \
          " 1_avg 1_min 1_1 1_25 1_50 1_75 1_99 1_max"
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
  (fn_dstat, num_stgdevs) = DstatLog.GetPlotFn(fn_ycsb)

  col_time = 17

  col_cpu_idle = 19
  col_cpu_sys  = col_cpu_idle + 2
  col_cpu_user = col_cpu_idle + 3
  col_cpu_iowait = col_cpu_idle + 4

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

      cpu = 100.0 - float(t[col_cpu_idle - 1])

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
