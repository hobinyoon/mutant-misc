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
    ycsb_logs = {}
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
    self.fn = fn
    # In us
    self.r_raw = []
    self.w_raw = []
    self.r_stat = None
    with open(fn) as fo:
      for line in fo:
        #Cons.P(line)
        if line.startswith("Command line: "):
          self._ParseOptions(line)
          continue
        elif line.startswith("[READ], "):
          # [READ], AverageLatency(us), 451.25953237986903
          mo = re.match(r"\[READ\], AverageLatency\(us\), (?P<v>(\d|\.)+).*", line)
          if mo is not None:
            self.r_avg = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], MinLatency\(us\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_min = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], MaxLatency\(us\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_max = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], 95thPercentileLatency\(us\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_95 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], 99thPercentileLatency\(us\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_99 = float(mo.group("v"))
            continue
        elif line.startswith("[OVERALL], "):
          mo = re.match(r"\[OVERALL\], Throughput\(ops\/sec\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.op_sec = float(mo.group("v"))
            continue
        elif line.startswith("READ,"):
          t = line.split(",")
          self.r_raw.append(int(t[2]))
        elif line.startswith("INSERT,"):
          t = line.split(",")
          self.w_raw.append(int(t[2]))

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

  def ReadLat(self):
    if self.r_stat is not None:
      return self.r_stat
    with Cons.MT("Generating read latency stat ..."):
      self.r_stat = Stat.Gen(self.r_raw)
      return self.r_stat

  def WriteLat(self):
    if self.w_stat is not None:
      return self.w_stat
    with Cons.MT("Generating write latency stat ..."):
      self.w_stat = Stat.Gen(self.w_raw)
      return self.w_stat

  def __repr__(self):
    return " ".join("%s=%s" % (k, v) for k, v in sorted(vars(self).iteritems()))


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
