#!/usr/bin/env python

import math
import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Stat

_dn_output = "%s/.output" % os.path.dirname(__file__)


def main(argv):
  Util.MkDirs(_dn_output)
  fn_plot_data = GetPlotData()
  fn_out = "%s/ycsb-d-read-thrp-vs-lat.pdf" % _dn_output
  # TODO: rename to contain st1

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["FN_IN"] = fn_plot_data
    env["FN_OUT"] = fn_out
    Util.RunSubp("gnuplot %s/ycsb-thrp-vs-lat.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def GetPlotData():
  fn_out = "%s/ycsb-d-by-iops" % _dn_output
  if os.path.isfile(fn_out):
    return fn_out

  with Cons.MT("Generating plot data ..."):
    # Parse YCSB log files and group by target IOPSes
    dt_ycsblog = {}
    targetiops_dt = {}
    dn_log = Conf.Get("RocksDB on st1").replace("~", os.path.expanduser("~"))
    for exp_id in os.listdir(dn_log):
      # exp_id: 170805-180831
      dn1 = "%s/%s/ycsb" % (dn_log, exp_id)
      for fn0 in os.listdir(dn1):
        fn = "%s/%s" % (dn1, fn0)
        if fn.endswith(".bz2"):
          fn1 = fn[:-4]
          if not os.path.exists(fn1):
            Util.RunSubp("pbzip2 -k -d %s" % fn)
          ycsb_log = YcsbLog(fn1)
          #Cons.P(ycsb_log)
          dt_ycsblog[ycsb_log.exp_dt] = ycsb_log
          if ycsb_log.target_iops not in targetiops_dt:
            targetiops_dt[ycsb_log.target_iops] = []
          targetiops_dt[ycsb_log.target_iops].append(ycsb_log.exp_dt)
    #Cons.P(pprint.pformat(dt_ycsblog))
    #Cons.P(pprint.pformat(targetiops_dt))


    with open(fn_out, "w") as fo:
      fmt = "%6d %6.0f" \
          " %5.0f %2d %8d %2d %2d %2d %3d %4d %6d %7d %8d" \
          " %5.0f %2d %8d %2d %2d %2d %3d %6d %6d %7d %8d" \
          " %1d"
      header = Util.BuildHeader(fmt, "target_iops iops" \
          " r_avg r_min r_max r_1p r_5p r_50p r_90p r_95p r_99p r_99.9p r_99.99p" \
          " w_avg w_min w_max w_1p w_5p w_50p w_90p w_95p w_99p w_99.9p w_99.99p" \
          " num_exps" \
          )
      #Cons.P(header)
      fo.write("# Latency in us\n")
      fo.write("#\n")
      fo.write(header + "\n")
      for ti, dts in sorted(targetiops_dt.iteritems()):
        yas = YcsbAvgStat()
        for dt in dts:
          yas.Add(dt_ycsblog[dt])
        yas.Calc()
        #Cons.P("%d %s" % (ti, yas))
        fo.write((fmt + "\n") % (ti, yas.op_sec
           , yas.r_avg, yas.r_min, yas.r_max, yas.r_1, yas.r_5, yas.r_50, yas.r_90, yas.r_95, yas.r_99, yas.r_999, yas.r_9999
           , yas.w_avg, yas.w_min, yas.w_max, yas.w_1, yas.w_5, yas.w_50, yas.w_90, yas.w_95, yas.w_99, yas.w_999, yas.w_9999
           , len(yas.logs)
           ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out







#      for ti, v in sorted(ycsb_logs.iteritems()):
#        r = v.ReadLat()
#        w = v.WriteLat()
#        fo.write((fmt + "\n") % (ti, v.op_sec
#          , r.avg, r._1, r._25, r._50, r._75, r._90, r._99, r._999, r._9999
#          , w.avg, w._1, w._25, w._50, w._75, w._90, w._99, w._999, w._9999
#          ))


      # TODO: Individual stats too




    sys.exit(0)




    sys.exit(0)

    fns_log = Conf.Get("RocksDB with local SSD")
    #Cons.P(pprint.pformat(fns_log))
    for fn in fns_log:
      fn = fn.replace("~", os.path.expanduser("~"))
      if not os.path.isfile(fn):
        if not os.path.isfile("%s.bz2" % fn):
          raise RuntimeError("Unexpected")
        Util.RunSubp("cd && pbzip2 -d %s.bz2" % (os.path.dirname(fn), fn))
      ycsb_log = YcsbLog(fn)
      #Cons.P(ycsb_log)
      ycsb_logs[ycsb_log.target_iops] = ycsb_log
    #Cons.P(pprint.pformat(ycsb_logs))

    fmt = "%6d %10.3f" \
        " %8.3f %3.0f %5.0f %5.0f %5.0f %6.0f %6.0f %6.0f %6.0f" \
        " %8.3f %3.0f %5.0f %5.0f %5.0f %6.0f %6.0f %6.0f %6.0f"
    with open(fn_out, "w") as fo:
      fo.write("# Latency in us\n")
      fo.write("%s\n" % Util.BuildHeader(fmt, "target_iops iops" \
          " r_avg r_1 r_25 r_50 r_75 r_90 r_99 r_99.9 r_99.99" \
          " w_avg w_1 w_25 w_50 w_75 w_90 w_99 w_99.9 w_99.99"))
      for ti, v in sorted(ycsb_logs.iteritems()):
        r = v.ReadLat()
        w = v.WriteLat()
        fo.write((fmt + "\n") % (ti, v.op_sec
          , r.avg, r._1, r._25, r._50, r._75, r._90, r._99, r._999, r._9999
          , w.avg, w._1, w._25, w._50, w._75, w._90, w._99, w._999, w._9999
          ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out


class YcsbLog:
  def __init__(self, fn):
    # /home/hobin/work/mutant/log/ycsb/d-thrp-vs-lat/rocksdb-st1/good/170805-180831/ycsb/170805-224531.277-d
    self.fn = fn
    fn0 = os.path.basename(fn)
    #Cons.P(fn0)
    if fn0.endswith("-d"):
      self.exp_dt = fn0[:-2]
      #Cons.P(self.exp_dt)

    with open(fn) as fo:
      for line in fo:
        #Cons.P(line)
        if line.startswith("Command line: "):
          self._ParseOptions(line)
          continue
        elif line.startswith("[READ], "):
          # In us
          # [READ], Average, 9720.066147407726
          # [READ], Min, 2
          # [READ], Max, 12472479
          # [READ], p1, 3
          # [READ], p5, 3
          # [READ], p50, 5
          # [READ], p90, 119
          # [READ], p95, 175
          # [READ], p99, 266929
          # [READ], p99.9, 1263474
          # [READ], p99.99, 2521401
          mo = re.match(r"\[READ\], Average, (?P<v>(\d|\.)+).*", line)
          if mo is not None:
            self.r_avg = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], Min, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_min = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], Max, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_max = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p1, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_1 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p5, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_5 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p50, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_50 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p90, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_90 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p95, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_95 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_99 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99\.9, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_999 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99\.99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_9999 = float(mo.group("v"))
            continue
        elif line.startswith("[INSERT], "):
          mo = re.match(r"\[INSERT\], Average, (?P<v>(\d|\.)+).*", line)
          if mo is not None:
            self.w_avg = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], Min, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_min = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], Max, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_max = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p1, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_1 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p5, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_5 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p50, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_50 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p90, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_90 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p95, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_95 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_99 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99\.9, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_999 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99\.99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_9999 = float(mo.group("v"))
            continue
        elif line.startswith("[OVERALL], "):
          mo = re.match(r"\[OVERALL\], Throughput\(ops\/sec\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.op_sec = float(mo.group("v"))
            continue

  def _ParseOptions(self, line):
    # -db com.yahoo.ycsb.db.RocksDBClient -s -P workloads/workloadd -p rocksdb.dir=/mnt/local-ssd1/rocksdb-data/ycsb -threads 100 -p
    # status.interval=1 -p fieldcount=10 -p fieldlength=100 -p readproportion=0.95 -p insertproportion=0.05 -p recordcount=10000000 -p
    # operationcount=30000000 -p readproportion=0.95 -p insertproportion=0.05 -target 130000 -t
    mo = re.match(r".+ -P (?P<workload_type>(\w|\/)+)" \
        ".* -target (?P<target_iops>\d+).*", line)
    # Make sure it's workload d
    if mo.group("workload_type") != "workloads/workloadd":
      raise RuntimeError("Unexpected")
    self.target_iops = int(mo.group("target_iops"))

  def __repr__(self):
    return " ".join("%s=%s" % (k, v) for k, v in sorted(vars(self).iteritems()))


class YcsbAvgStat:
  def __init__(self):
    self.logs = []

  def Add(self, ycsb_log):
    self.logs.append(ycsb_log)

  def Calc(self):
    op_sec = []
    r_1 = []
    r_5 = []
    r_50 = []
    r_90 = []
    r_95 = []
    r_99 = []
    r_999 = []
    r_9999 = []
    r_avg = []
    r_max = []
    r_min = []
    w_1 = []
    w_5 = []
    w_50 = []
    w_90 = []
    w_95 = []
    w_99 = []
    w_999 = []
    w_9999 = []
    w_avg = []
    w_max = []
    w_min = []
    for l in self.logs:
      # exp_dt=170805-233212.730 fn=/home/hobin/work/mutant/log/ycsb/d-thrp-vs-lat/rocksdb-st1/good/170805-180749/ycsb/170805-233212.730-d
      # op_sec=9902.92165898 r_1=3.0 r_5=3.0 r_50=7.0 r_90=135.0 r_95=207.0 r_99=257710.0 r_999=1222746.0 r_9999=2552744.0
      # r_avg=9529.4250367 r_max=14803272.0 r_min=2.0 target_iops=10000 w_1=15.0 w_5=17.0 w_50=26.0 w_90=54.0 w_95=80.0 w_99=274649.0
      # w_999=933013.0 w_9999=2261246.0 w_avg=8020.84528045 w_max=4506480.0 w_min=11.0
      op_sec.append(l.op_sec)
      r_1   .append(l.r_1   )
      r_5   .append(l.r_5   )
      r_50  .append(l.r_50  )
      r_90  .append(l.r_90  )
      r_95  .append(l.r_95  )
      r_99  .append(l.r_99  )
      r_999 .append(l.r_999 )
      r_9999.append(l.r_9999)
      r_avg .append(l.r_avg )
      r_max .append(l.r_max )
      r_min .append(l.r_min )
      w_1   .append(l.w_1   )
      w_5   .append(l.w_5   )
      w_50  .append(l.w_50  )
      w_90  .append(l.w_90  )
      w_95  .append(l.w_95  )
      w_99  .append(l.w_99  )
      w_999 .append(l.w_999 )
      w_9999.append(l.w_9999)
      w_avg .append(l.w_avg )
      w_max .append(l.w_max )
      w_min .append(l.w_min )
    self.op_sec = sum(op_sec) / len(op_sec)
    self.r_1    = sum(r_1   ) / len(r_1   )
    self.r_5    = sum(r_5   ) / len(r_5   )
    self.r_50   = sum(r_50  ) / len(r_50  )
    self.r_90   = sum(r_90  ) / len(r_90  )
    self.r_95   = sum(r_95  ) / len(r_95  )
    self.r_99   = sum(r_99  ) / len(r_99  )
    self.r_999  = sum(r_999 ) / len(r_999 )
    self.r_9999 = sum(r_9999) / len(r_9999)
    self.r_avg  = sum(r_avg ) / len(r_avg )
    self.r_max  = sum(r_max ) / len(r_max )
    self.r_min  = sum(r_min ) / len(r_min )
    self.w_1    = sum(w_1   ) / len(w_1   )
    self.w_5    = sum(w_5   ) / len(w_5   )
    self.w_50   = sum(w_50  ) / len(w_50  )
    self.w_90   = sum(w_90  ) / len(w_90  )
    self.w_95   = sum(w_95  ) / len(w_95  )
    self.w_99   = sum(w_99  ) / len(w_99  )
    self.w_999  = sum(w_999 ) / len(w_999 )
    self.w_9999 = sum(w_9999) / len(w_9999)
    self.w_avg  = sum(w_avg ) / len(w_avg )
    self.w_max  = sum(w_max ) / len(w_max )
    self.w_min  = sum(w_min ) / len(w_min )

  def __repr__(self):
    #return " ".join("%s=%s" % (k, v) for k, v in sorted(vars(self).iteritems()))

    kv = {}
    for k, v in sorted(vars(self).iteritems()):
      if k.startswith("r_") or k.startswith("w_"):
        kv[k] = v
    return " ".join("%s=%s" % (k, v) for k, v in sorted(kv.iteritems()))


class StatPerSec:
  fmt = "%5d %5d %8.2f %5d %8.2f %5d"

  def __init__(self, line):
    #Cons.P(line)
    # 2016-09-12 23:50:15:208 1 sec: 1950 operations; 1948.05 current ops/sec;
    # est completion in 14 hours 15 minutes [READ: Count=1842, Max=120063,
    # Min=6640, Avg=24343.08, 90=43007, 99=114687, 99.9=118527, 99.99=120063]
    # [INSERT: Count=112, Max=118655, Min=8216, Avg=25360.89, 90=43807,
    # 99=117951, 99.9=118655, 99.99=118655]
    mo = re.match(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d:\d\d\d (?P<timestamp>\d+) sec: \d+ operations; (\d|\.)+ current ops/sec; .+" \
        "READ: Count=(?P<read_iops>\d+), Max=\d+, Min=\d+, Avg=(?P<read_lat_avg>\S+) .+" \
        "INSERT: Count=(?P<ins_iops>\d+).+ Avg=(?P<ins_lat_avg>\S+)"
        , line)
    if mo is None:
      raise RuntimeError("Unexpected [%s]" % line)

    self.timestamp = int(mo.group("timestamp"))
    self.read_iops = int(mo.group("read_iops"))
    if self.read_iops == 0:
      self.read_lat_avg = 0
    else:
      try:
        self.read_lat_avg = float(mo.group("read_lat_avg")[:-1])
      except ValueError as e:
        Cons.P("%s [%s]" % (e, line))
        sys.exit(0)
    self.ins_iops = int(mo.group("ins_iops"))
    if self.ins_iops == 0:
      self.ins_lat_avg = 0
    else:
      self.ins_lat_avg = float(mo.group("ins_lat_avg")[:-1])
    self.iops = self.read_iops + self.ins_iops

  @staticmethod
  def WriteHeader(fo):
    fo.write("%s\n" % Util.BuildHeader(StatPerSec.fmt,
      "timestamp_in_sec"
      " read_iops"
      " read_lat_avg_in_us"
      " ins_iops"
      " ins_lat_avg_in_us"
      " iops"
      ))

  def __str__(self):
    return StatPerSec.fmt % \
        (self.timestamp
            , self.read_iops
            , self.read_lat_avg
            , self.ins_iops
            , self.ins_lat_avg
            , self.iops
            )


if __name__ == "__main__":
  sys.exit(main(sys.argv))
