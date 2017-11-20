#!/usr/bin/env python

import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Stat

_dn_output = "%s/.output" % os.path.dirname(__file__)


def main(argv):
  Util.MkDirs(_dn_output)

  # CDFs for 4k reads and 64m writes for local SSD and EBS st1.

  ReadStat([
        {"Local SSD": "raw-data/4k-randread-ioping-localssd"}
        , {"EBS st1": "raw-data/4k-randread-ioping-ebsst1"}
      ])

  WriteStat([
        {"Local SSD": "raw-data/64m-write-local-ssd"}
        , {"EBS st1": "raw-data/64m-write-st1"}
      ])


class WriteStat():
  def __init__(self, logs):
    with Cons.MT("Read stat:", print_time=False):
      self.fns_cdf = []

      self.logs = logs
      for l in logs:
        self.GenStat(l.itervalues().next())
      self.PlotCDF()
      #self.PlotByTime()

  def GenStat(self, fn):
    with Cons.MT(fn, print_time=False):
      thrp = []
      with open(fn) as fo:
        for line in fo.readlines():
          line = line.rstrip()
          if len(line) == 0:
            continue
          if line.startswith("#"):
            continue

          # 0.348919 s, 192 MB/s
          m = re.match(r"(?P<lap_time>(\d|\.)+) s, .+", line)
          if m:
            thrp.append(64.0 / float(m.group("lap_time")))
            continue
          raise RuntimeError("Unexpected %s" % line)
      #Cons.P(len(thrp))
      fn_cdf = "%s/%s-cdf" % (_dn_output, os.path.basename(fn))
      self.fns_cdf.append(fn_cdf)
      Stat.GenStat(thrp, fn_cdf)

      # Throughput in the time order
      #fn_time_order = "%s/%s-time-order" % (_dn_output, fn)
      #with open(fn_time_order, "w") as fo:
      #  for t in thrp:
      #    fo.write("%s\n" % t)
      #Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

  def PlotCDF(self):
    fn_out = "%s/64m-write-thrp-localssd-ebsst1.pdf" % _dn_output

    with Cons.MT("Plotting 128mb write throughput CDF by storage ..."):
      env = os.environ.copy()
      env["FN_IN_LS"] = self.fns_cdf[0]
      env["FN_IN_EST1"] = self.fns_cdf[1]
      env["FN_OUT"] = fn_out
      Util.RunSubp("gnuplot %s/write-thrp-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

  def PlotByTime(self):
    with Cons.MT("Plotting 128mb write throughput by time by storage ..."):
      fn_in = " ".join("%s/%s-time-order" % (_dn_output, l.itervalues().next()) for l in self.logs)
      fn_out = "%s/128mb-write-thrp-by-time-by-storage.pdf" % _dn_output

      env = os.environ.copy()
      env["FN_IN"] = fn_in
      env["FN_OUT"] = fn_out
      Util.RunSubp("gnuplot %s/seq-write-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


class ReadStat():
  def __init__(self, logs):
    with Cons.MT("Read stat:", print_time=False):
      self.fns_cdf = []

      self.logs = logs
      for l in logs:
        self.GenStat(l.itervalues().next())
      self.PlotCDF()

      # Hard to interprete with 4 different types
      #self.PlotByTimeByStorage()

      #self.PlotByTime()

  def GenStat(self, fn):
    with Cons.MT(fn, print_time=False):
      lap_times = []
      with open(fn) as fo:
        for line in fo.readlines():
          line = line.rstrip()
          if len(line) == 0:
            continue
          if line.startswith("#"):
            continue

          # 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=1 time=219.1 us
          # 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=394 time=1.51 ms
          m = re.match(r"(?P<lap_time>(\d|\.)+ (us|ms))", line)
          if m:
            lt = m.group("lap_time")
            if lt.endswith(" us"):
              lt = float(lt[:-3])
            elif lt.endswith(" ms"):
              lt = (float(lt[:-3]) * 1000)
            lap_times.append(lt)
            continue

          raise RuntimeError("Unexpected [%s]" % line)
      #Cons.P(len(lap_times))
      fn_cdf = "%s/%s-cdf" % (_dn_output, os.path.basename(fn))
      self.fns_cdf.append(fn_cdf)
      Stat.GenStat(lap_times, fn_cdf)

      # Throughput in the time order
      #fn_time_order = "%s/%s-time-order" % (_dn_output, fn)
      #with open(fn_time_order, "w") as fo:
      #  for t in lap_times:
      #    fo.write("%s\n" % t)
      #Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

  def PlotCDF(self):
    fn_out = "%s/4k-randread-lat-localssd-ebsst1.pdf" % _dn_output

    with Cons.MT("Plotting CDF by storage ..."):
      env = os.environ.copy()
      env["FN_IN_LS"] = self.fns_cdf[0]
      env["FN_IN_EST1"] = self.fns_cdf[1]
      env["FN_OUT"] = fn_out
      Util.RunSubp("gnuplot %s/randread-lat-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

  def PlotByTimeByStorage(self):
    with Cons.MT("Plotting by time by storage ..."):
      fn_in = " ".join("%s/%s-time-order" % (_dn_output, l.itervalues().next()) for l in self.logs)
      keys = " ".join(l.iterkeys().next().replace("_", "\\_") for l in self.logs)
      fn_out = "%s/4kb-read-latency-by-time-by-storages.pdf" % _dn_output

      env = os.environ.copy()
      env["FN_IN"] = fn_in
      env["KEYS"] = keys
      env["FN_OUT"] = fn_out
      Util.RunSubp("gnuplot %s/rand-read-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

  def PlotByTime(self):
    with Cons.MT("Plotting by time by storage ..."):
      i = 0
      for l in self.logs:
        i += 1
        fn_in = "%s/%s-time-order" % (_dn_output, l.itervalues().next())
        key = l.iterkeys().next()
        fn_out = "%s/4kb-read-latency-by-time-%s.pdf" % (_dn_output, key.replace(" ", "-"))

        env = os.environ.copy()
        env["FN_IN"] = fn_in
        env["KEY"] = key
        env["FN_OUT"] = fn_out
        env["KEY_IDX"] = str(i)
        env["Y_LABEL_COLOR"] = "black" if key == "Local SSD" else "white"
        Util.RunSubp("gnuplot %s/rand-read-by-time-single-storage.gnuplot" % os.path.dirname(__file__), env=env)
        Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
