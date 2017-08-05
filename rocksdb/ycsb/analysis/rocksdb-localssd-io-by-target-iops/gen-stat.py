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
  DiskIOsByTargetIOPSes()


def DiskIOsByTargetIOPSes():
  with Cons.MT("Calc ..."):
    ycsb_logs = {}
    fns_log0 = Conf.Get("Disk IO by target IOPS. RocksDB with Local SSD. YCSB workload d")
    #Cons.P(pprint.pformat(fns_log))

    # Match ycsb and dstat log pairs
    dt_ycsbfn = {}
    dt_dstatfn = {}
    for fn in fns_log0:
      log_type = os.path.basename(os.path.dirname(fn))
      if log_type == "ycsb":
        #Cons.P(fn)
        # ~/work/mutant/misc/rocksdb/ycsb/logs/workload-d-by-target-iops/170805-101952/ycsb/170805-151806.933-d
        dt = os.path.basename(fn)
        if not dt.endswith("-d"):
          raise RuntimeError("Unexpected [%s]" % fn)
        dt = dt[:-2]
        dt_ycsbfn[dt] = fn
      elif log_type == "dstat":
        dt = os.path.basename(fn)
        if not dt.endswith(".csv"):
          raise RuntimeError("Unexpected [%s]" % fn)
        dt = dt[:-4]
        dt_dstatfn[dt] = fn

    # Make sure of they match 1:1
    if len(dt_ycsbfn) != len(dt_dstatfn):
      raise RuntimeError("Unexpected")
    for dt, fn in dt_ycsbfn.iteritems():
      if dt not in dt_dstatfn:
        raise RuntimeError("Unexpected")

    dt_ycsblog = {}
    dt_dstatlog = {}
    targetiops_dt = {}
    # Parse YCSB and Dstat logs. Group exp datetimes by target_iops.
    for dt, fn in dt_ycsbfn.iteritems():
      fn = fn.replace("~", os.path.expanduser("~"))
      if not os.path.isfile(fn):
        if not os.path.isfile("%s.bz2" % fn):
          raise RuntimeError("Unexpected [%s]" % fn)
        Util.RunSubp("cd %s && pbzip2 -d %s.bz2" % (os.path.dirname(fn), fn))
      ycsb_log = YcsbLog(fn)
      #Cons.P(ycsb_log)
      dt_ycsblog[dt] = ycsb_log
      target_iops = ycsb_log.target_iops
      if target_iops not in targetiops_dt:
        targetiops_dt[target_iops] = []
      targetiops_dt[target_iops].append(dt)

      fn = dt_dstatfn[dt]
      fn = fn.replace("~", os.path.expanduser("~"))
      if not os.path.isfile(fn):
        if not os.path.isfile("%s.bz2" % fn):
          raise RuntimeError("Unexpected [%s]" % fn)
        Util.RunSubp("cd %s && pbzip2 -d %s.bz2" % (os.path.dirname(fn), fn))
      dstat_log = DstatLog(fn)
      dt_dstatlog[dt] = dstat_log
      #Cons.P(dstat_log)

    fmt = "%6d %17s %6.0f %4.1f %4.1f %5.1f %5.1f"
    Cons.P(Util.BuildHeader(fmt, "target_iops datetime IOPS r_avg(MB/sec) r_50 r_90 r_99"))
    for target_iops, dts in sorted(targetiops_dt.iteritems()):
      for dt in dts:
        r = dt_dstatlog[dt].r_stat
        Cons.P(fmt % (target_iops, dt, dt_ycsblog[dt].op_sec
          , (r.avg/1024.0/1024)
          , (r._50/1024.0/1024)
          , (r._90/1024.0/1024)
          , (r._99/1024.0/1024)))
      print ""


class YcsbLog:
  def __init__(self, fn):
    self.fn = fn
    with open(fn) as fo:
      for line in fo:
        #Cons.P(line)
        if line.startswith("Command line: "):
          self._ParseOptions(line)
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


class DstatLog:
  def __init__(self, fn):
    self.fn = fn
    #Cons.P(fn)
    # IO in bytes/sec
    r_raw = []
    w_raw = []
    with open(fn) as fo:
      idx_xvdc = -1
      for line in fo:
        #Cons.P(line)
        if line.startswith("\"system\","):
          #Cons.P(line)
          tokens = line.split(",")
          for i in range(len(tokens)):
            if tokens[i] == "\"dsk/xvdc\"":
              idx_xvdc = i
              break
        if (idx_xvdc != -1) and (line[0] != "\""):
          #Cons.P(line)
          tokens = line.split(",")
          r_raw.append(float(tokens[idx_xvdc]))
          w_raw.append(float(tokens[idx_xvdc + 1]))
    self.r_stat = Stat.Gen(r_raw)
    self.w_stat = Stat.Gen(w_raw)

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
