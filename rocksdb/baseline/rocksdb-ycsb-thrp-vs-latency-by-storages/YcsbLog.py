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
import Stat


def GenDataThrpVsLat():
  fn_out = "%s/rocksdb-ycsb-thrp-vs-lat-by-stgdevs" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating thrp vs lat data file ..."):
    dn_base = Conf.GetDir("dn_base")

    # {stg_dev: {target_iops: YcsbLogReader}}
    stgdev_tio_ylr = {}

    for stgdev in ["local-ssd", "ebs-st1"]:
      if stgdev not in stgdev_tio_ylr:
        stgdev_tio_ylr[stgdev] = {}

      for target_iops, v in sorted(Conf.Get(stgdev).iteritems()):
        fn = "%s/%s" % (dn_base, v["fn"])
        t = v["time"].split("-")
        time_begin = t[0]
        time_end = t[1]
        #Cons.P("%s %s %s" % (fn, time_begin, time_end))
        stgdev_tio_ylr[stgdev][target_iops] = YcsbLogReader(fn, time_begin, time_end)

    with open(fn_out, "w") as fo:
      fmt = "%9s %6.0f %6.0f" \
          " %8.2f %8.2f %9.2f %10.2f %10.2f" \
          " %8.2f %8.2f %8.2f %9.2f %9.2f"
      fo.write("%s\n" % Util.BuildHeader(fmt, "stg_dev target_iops iops" \
          " r_avg r_90 r_99 r_99.9 r_99.99" \
          " w_avg w_90 w_99 w_99.9 w_99.99"
          ))
      for stgdev, v in sorted(stgdev_tio_ylr.iteritems()):
        for tio, ylr in sorted(v.iteritems()):
          fo.write((fmt + "\n") % (
            stgdev
            , tio
            , ylr.db_iops_stat.avg
            , ylr.r_avg
            , ylr.r_90
            , ylr.r_99
            , ylr.r_999
            , ylr.r_9999
            , ylr.w_avg
            , ylr.w_90
            , ylr.w_99
            , ylr.w_999
            , ylr.w_9999
            ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out


# Generate a formatted output file for gnuplot. The csv file has headers that's not ideal for gnuplot.
#def GenDataMetricsByTime(fn_in, exp_dt):
#  lr = YcsbLogReader(fn_in, exp_dt)
#  return (lr.FnMetricByTime(), lr.TimeMax(), lr.GetParams())


def GenDataCostVsMetrics(exp_set_id):
  fn_out = "%s/rocksdb-ycsb-cost-vs-perf-%s" % (Conf.GetOutDir(), exp_set_id)

  fmt = "%5s %5.3f" \
      " %14.6f" \
      " %14.6f" \
      " %14.6f" \
      " %14.6f" \
      " %14.6f" \
      " %14.6f" \
      " %13.6f %10.6f %14.6f %14.6f %14.6f %14.6f %14.6f" \
      " %13.6f %10.6f %14.6f %14.6f %14.6f %14.6f %14.6f"
  with open(fn_out, "w") as fo:
    fo.write(Util.BuildHeader(fmt, "stg_dev cost_dollar_per_gb_per_month" \
        " db_iops.avg" \
        " db_iops.min" \
        " db_iops.max" \
        " db_iops._25" \
        " db_iops._50" \
        " db_iops._75" \
        " r_avg r_min r_max r_90 r_99 r_999 r_9999" \
        " w_avg w_min w_max w_90 w_99 w_999 w_9999"
        ) + "\n")
    for stg_dev, v in Conf.Get(exp_set_id).iteritems():
      lr = YcsbLogReader(exp_set_id, stg_dev)
      fo.write((fmt + "\n") % (
        stg_dev, float(Conf.Get("stg_cost")[stg_dev])
        , lr.GetStat("db_iops.avg")
        , lr.GetStat("db_iops.min")
        , lr.GetStat("db_iops.max")
        , lr.GetStat("db_iops._25")
        , lr.GetStat("db_iops._50")
        , lr.GetStat("db_iops._75")
        , lr.GetStat("r_avg")
        , lr.GetStat("r_min")
        , lr.GetStat("r_max")
        , lr.GetStat("r_90")
        , lr.GetStat("r_99")
        , lr.GetStat("r_999")
        , lr.GetStat("r_9999")
        , lr.GetStat("w_avg")
        , lr.GetStat("w_min")
        , lr.GetStat("w_max")
        , lr.GetStat("w_90")
        , lr.GetStat("w_99")
        , lr.GetStat("w_999")
        , lr.GetStat("w_9999")
        ))
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


class YcsbLogReader:
  def __init__(self, fn_in, time_begin, time_end):
    # Unzip when the file is not there
    if not os.path.exists(fn_in):
      fn_zipped = "%s.bz2" % fn_in
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn_in)
      Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn_in):
      raise RuntimeError("Unexpected")
    #Cons.P(fn_in)

    mo_list = []
    line_params = None
    line_run = None
    with open(fn_in) as fo:
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
        if mo is None:
          continue

        total_seconds = int(mo.group("rel_time"))
        s = total_seconds % 60
        total_seconds -= s
        total_mins = total_seconds / 60
        m = total_mins % 60
        total_mins -= m
        h = total_mins / 60
        rel_time = "%02d:%02d:%02d" % (h, m, s)
        if (time_begin <= rel_time) and (rel_time <= time_end):
          mo_list.append((rel_time, mo))
    if len(mo_list) == 0:
      raise RuntimeError("Unexpected. Check file [%s]" % fn_in)

    cnt = 0
    db_iops = []
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
      mo = e[1]
      db_iops.append(float(mo.group("db_iops")))
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

    self.db_iops_stat = Stat.Gen(db_iops)

    self.r_cnt  = r_cnt
    self.r_avg  = (float(r_avg ) / cnt)
    self.r_min  = (float(r_min ) / cnt)
    self.r_max  = (float(r_max ) / cnt)
    self.r_90   = (float(r_90  ) / cnt)
    self.r_99   = (float(r_99  ) / cnt)
    self.r_999  = (float(r_999 ) / cnt)
    self.r_9999 = (float(r_9999) / cnt)
    self.w_cnt  = (float(w_cnt ) / cnt)
    self.w_avg  = (float(w_avg ) / cnt)
    self.w_min  = (float(w_min ) / cnt)
    self.w_max  = (float(w_max ) / cnt)
    self.w_90   = (float(w_90  ) / cnt)
    self.w_99   = (float(w_99  ) / cnt)
    self.w_999  = (float(w_999 ) / cnt)
    self.w_9999 = (float(w_9999) / cnt)
