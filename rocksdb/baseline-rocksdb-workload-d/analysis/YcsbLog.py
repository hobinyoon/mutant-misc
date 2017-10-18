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
def GenDataFileForGnuplot(dn_log_job, exp_dt):
  lr = YcsbLogReader(dn_log_job, exp_dt)
  return (lr.FnMetricByTime(), lr.TimeMax(), lr.GetParams())


class YcsbLogReader:
  def __init__(self, dn_log_job, exp_dt):
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
      with open(fn_log_ycsb) as fo, open(self.fn_out, "w") as fo_out:
        fo_out.write(header + "\n")

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

            fo_out.write((fmt + "\n") % (
              rel_time , float(mo.group("db_iops"))
              , int(mo.group("r_cnt")) , float(mo.group("r_avg")) , int(mo.group("r_min")) , int(mo.group("r_max"))
              , int(mo.group("r_90")) , int(mo.group("r_99")) , int(mo.group("r_999")) , int(mo.group("r_9999"))
              , int(mo.group("w_cnt")) , float(mo.group("w_avg")) , int(mo.group("w_min")) , int(mo.group("w_max"))
              , int(mo.group("w_90")) , int(mo.group("w_99")) , int(mo.group("w_999")) , int(mo.group("w_9999"))
              ))
            continue

          if line.startswith("params = {"):
            fo_out.write("# %s" % line)
            continue

          if line.startswith("run = {"):
            fo_out.write("# %s" % line)
            continue

      Cons.P("Created %s %d" % (self.fn_out, os.path.getsize(self.fn_out)))

  def FnMetricByTime(self):
    return self.fn_out

  def TimeMax(self):
    time = None
    with open(self.fn_out) as fo:
      for line in fo:
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
