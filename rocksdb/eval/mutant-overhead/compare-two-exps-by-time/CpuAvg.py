import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog

# Note: This depends on the DstatLog output file format
def GetFnForPlot(fn_ycsb, exp_dt):
  fn_out = "%s/cpu-avg-%s" % (Conf.GetOutDir(), exp_dt)
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Creating avg cpu usage file for plotting ..."):
    (fn_dstat, num_stgdevs) = DstatLog.GetPlotFn(fn_ycsb)

    col_time = 17

    col_cpu_idle = 19
    col_cpu_sys  = col_cpu_idle + 2
    col_cpu_user = col_cpu_idle + 3
    col_cpu_iowait = col_cpu_idle + 4

    # {hour_minute: [cpu_usage]}
    hm_cpu = {}
    with open(fn_dstat) as fo:
      for line in fo:
        if line.startswith("#"):
          continue
        line = line.strip()
        t = re.split(r" +", line)

        # Parse these cause some hours and mins don't have left padding 0s.
        mo = re.match(r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)", t[col_time - 1])
        hour = int(mo.group("h"))
        minute = int(mo.group("m"))
        hour_minute = "%02d:%02d" % (hour, minute)

        cpu = 100.0 - float(t[col_cpu_idle - 1])

        if hour_minute not in hm_cpu:
          hm_cpu[hour_minute] = []
        hm_cpu[hour_minute].append(cpu)

    fmt = "%5s %6.2f"
    header = Util.BuildHeader(fmt, "hour_min cpu_avg")

    with open(fn_out, "w") as fo:
      i = 0
      for hm, v in sorted(hm_cpu.iteritems()):
        if i % 40 == 0:
          fo.write(header + "\n")
        i += 1
        l = len(v)
        avg = 0 if l == 0 else (float(sum(v)) / l)
        fo.write((fmt + "\n") % (hm, avg))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out
