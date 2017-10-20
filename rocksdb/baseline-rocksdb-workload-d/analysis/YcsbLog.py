import ast
import csv
import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


# These are not thread-safe. Okay for now.
_num_stg_devs = 0
_body_rows = None

# Generate a formatted output file for gnuplot. The csv file has headers that's not ideal for gnuplot.
def GenDataFileForGnuplot(dn_log_job, exp_dt, exp_time_begin, exp_time_end):
  lr = YcsbLogReader(dn_log_job, exp_dt, exp_time_begin, exp_time_end)
  return (lr.FnMetricByTime(), lr.TimeMax(), lr.GetParams())


class YcsbLogReader:
  def __init__(self, dn_log_job, exp_dt, exp_time_begin, exp_time_end):
    self.fn_out = "%s/ycsb-by-time-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")
    #Cons.P(self.exp_begin_dt)

    with Cons.MT("Generating ycsb time-vs-metrics file for plot ..."):
      fn_log_ycsb = "%s/ycsb/%s-d" % (dn_log_job, exp_dt)
      # Unzip when the file is not there
      if not os.path.exists(fn_log_ycsb):
        fn_zipped = "%s.bz2" % fn_log_ycsb
        if not os.path.exists(fn_zipped):
          raise RuntimeError("Unexpected: %s" % fn_log_ycsb)
        Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
      if not os.path.exists(fn_log_ycsb):
        raise RuntimeError("Unexpected")

      mo_list = []
      line_params = None
      line_run = None
      with open(fn_log_ycsb) as fo:
        for line in fo:
          #Cons.P(line)
          # 2017-10-13 20:41:01:258 2 sec: 34 operations; 34 current ops/sec; est completion in 68 days 1 hours [READ: Count=28, Max=46943, Min=33,
          # Avg=32239.54, 90=45343, 99=46943, 99.9=46943, 99.99=46943] [INSERT: Count=8, Max=9343, Min=221, Avg=4660.88, 90=8695, 99=9343, 99.9=9343,
          # 99.99=9343]
          mo = re.match(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d:\d\d\d (?P<rel_time>\d+) sec: \d+ operations; " \
              "(?P<db_iops>(\d|\.)+) current ops\/sec; .*" \
              "\[READ: Count=(?P<r_cnt>\d+), Max=(?P<r_max>\d+), Min=(?P<r_min>\d+), Avg=(?P<r_avg>(\d|\.)+)," \
              " 90=(?P<r_90>\d+), 99=(?P<r_99>\d+), 99.9=(?P<r_999>\d+), 99.99=(?P<r_9999>\d+)\] " \
              "\[INSERT: Count=(?P<w_cnt>\d+), Max=(?P<w_max>\d+), Min=(?P<w_min>\d+), Avg=(?P<w_avg>(\d|\.)+)," \
              " 90=(?P<w_90>\d+), 99=(?P<w_99>\d+), 99.9=(?P<w_999>\d+), 99.99=(?P<w_9999>\d+)\] " \
              , line)
          if mo is not None:
            total_seconds = int(mo.group("rel_time"))
            s = total_seconds % 60
            total_seconds -= s
            total_mins = total_seconds / 60
            m = total_mins % 60
            total_mins -= m
            h = total_mins / 60
            rel_time = "%02d:%02d:%02d" % (h, m, s)
            mo_list.append((rel_time, mo))
            continue

          if line.startswith("params = {"):
            line_params = line
            continue

          if line.startswith("run = {"):
            line_run = line
            continue

      cnt = 0
      db_iops = 0.0
      r_cnt = 0
      r_avg = 0.0
      r_min = 0
      r_max = 0
      r_90  = 0
      r_99  = 0
      r_999 = 0
      r_9999 = 0
      w_cnt = 0
      w_avg = 0.0
      w_min = 0
      w_max = 0
      w_90  = 0
      w_99  = 0
      w_999 = 0
      w_9999 = 0
      for e in mo_list:
        rel_time = e[0]
        if (exp_time_begin < rel_time) and (rel_time < exp_time_end):
          mo = e[1]
          db_iops += float(mo.group("db_iops"))
          r_cnt   += int(mo.group("r_cnt"))
          r_avg   += float(mo.group("r_avg"))
          r_min   += int(mo.group("r_min"))
          r_max   += int(mo.group("r_max"))
          r_90    += int(mo.group("r_90"))
          r_99    += int(mo.group("r_99"))
          r_999   += int(mo.group("r_999"))
          r_9999  += int(mo.group("r_9999"))
          w_cnt   += int(mo.group("w_cnt"))
          w_avg   += float(mo.group("w_avg"))
          w_min   += int(mo.group("w_min"))
          w_max   += int(mo.group("w_max"))
          w_90    += int(mo.group("w_90"))
          w_99    += int(mo.group("w_99"))
          w_999   += int(mo.group("w_999"))
          w_9999  += int(mo.group("w_9999"))
          cnt += 1

      fmt = "%8s %9.2f" \
          " %6d %8.2f %3d %6d" \
          " %6d %6d %6d %6d" \
          " %6d %8.2f %3d %6d" \
          " %6d %6d %6d %6d"
      header = Util.BuildHeader(fmt, "rel_time db_iops" \
            " read_cnt read_lat_avg read_lat_min read_lat_max" \
            " read_lat_90p read_lat_99p read_lat_99.9p read_lat_99.99p" \
            " write_cnt write_lat_avg write_lat_min write_lat_max" \
            " write_lat_90p write_lat_99p write_lat_99.9p write_lat_99.99p" \
            )

      with open(self.fn_out, "w") as fo_out:
        fo_out.write("# %s" % line_params)
        fo_out.write("# %s" % line_run)
        fo_out.write("\n")
        fo_out.write("# In the time range (%s, %s):\n" % (exp_time_begin, exp_time_end))
        fo_out.write("#   db_iops= %13f\n" % (float(db_iops) / cnt))
        fo_out.write("#   r_cnt  = %13f\n" % (float(r_cnt ) / cnt))
        fo_out.write("#   r_avg  = %13f\n" % (float(r_avg ) / cnt))
        fo_out.write("#   r_min  = %13f\n" % (float(r_min ) / cnt))
        fo_out.write("#   r_max  = %13f\n" % (float(r_max ) / cnt))
        fo_out.write("#   r_90   = %13f\n" % (float(r_90  ) / cnt))
        fo_out.write("#   r_99   = %13f\n" % (float(r_99  ) / cnt))
        fo_out.write("#   r_999  = %13f\n" % (float(r_999 ) / cnt))
        fo_out.write("#   r_9999 = %13f\n" % (float(r_9999) / cnt))
        fo_out.write("#   w_cnt  = %13f\n" % (float(w_cnt ) / cnt))
        fo_out.write("#   w_avg  = %13f\n" % (float(w_avg ) / cnt))
        fo_out.write("#   w_min  = %13f\n" % (float(w_min ) / cnt))
        fo_out.write("#   w_max  = %13f\n" % (float(w_max ) / cnt))
        fo_out.write("#   w_90   = %13f\n" % (float(w_90  ) / cnt))
        fo_out.write("#   w_99   = %13f\n" % (float(w_99  ) / cnt))
        fo_out.write("#   w_999  = %13f\n" % (float(w_999 ) / cnt))
        fo_out.write("#   w_9999 = %13f\n" % (float(w_9999) / cnt))
        fo_out.write("\n")

        i = 0
        for e in mo_list:
          rel_time = e[0]
          mo = e[1]
          if i % 40 == 0:
            fo_out.write(header + "\n")
          fo_out.write((fmt + "\n") % (
            rel_time , float(mo.group("db_iops"))
            , int(mo.group("r_cnt")) , float(mo.group("r_avg")) , int(mo.group("r_min")) , int(mo.group("r_max"))
            , int(mo.group("r_90")) , int(mo.group("r_99")) , int(mo.group("r_999")) , int(mo.group("r_9999"))
            , int(mo.group("w_cnt")) , float(mo.group("w_avg")) , int(mo.group("w_min")) , int(mo.group("w_max"))
            , int(mo.group("w_90")) , int(mo.group("w_99")) , int(mo.group("w_999")) , int(mo.group("w_9999"))
            ))
          i += 1
      Cons.P("Created %s %d" % (self.fn_out, os.path.getsize(self.fn_out)))

  def FnMetricByTime(self):
    return self.fn_out

  def TimeMax(self):
    time = None
    with open(self.fn_out) as fo:
      for line in fo:
        line = line.strip()
        if len(line) == 0:
          continue
        if line.startswith("#"):
          continue
        t = re.split(r" +", line.strip())
        if len(t) != 18:
          raise RuntimeError("Unexpected: %d [%s]" % (len(t), line))
        time = t[0]
    return time

  def GetParams(self):
    params = None
    run = None
    with open(self.fn_out) as fo:
      for line in fo:
        if line.startswith("# params = {"):
          params = ast.literal_eval(line[11:])
          continue
        if line.startswith("# run = {"):
          run = ast.literal_eval(line[8:])
          continue
    return (params, run)
