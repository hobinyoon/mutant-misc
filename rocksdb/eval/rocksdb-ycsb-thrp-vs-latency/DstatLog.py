import csv
import datetime
import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


def GenDataThrpVsAllMetrics():
  fn_out = "%s/rocksdb-ycsb-thrp-vs-dstat-metrics-by-stgdevs" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating thrp vs dstat metrics data file ..."):
    dn_base = Conf.GetDir("dn_base")

    # {stg_dev: {target_iops: DstatLogReader}}
    stgdev_tio_dlr = {}

    for stgdev in ["local-ssd", "ebs-st1"]:
      if stgdev not in stgdev_tio_dlr:
        stgdev_tio_dlr[stgdev] = {}

      for target_iops, v in sorted(Conf.Get(stgdev).iteritems()):
        # 171125-110758/ycsb/171125-161934.339-d
        mo = re.match(r"(?P<dn>.+)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).*", v["fn"])
        dn = "%s/%s" % (dn_base, mo.group("dn"))
        exp_dt = mo.group("exp_dt")
        #Cons.P("%s %s" % (dn, exp_dt))

        t = v["time"].split("-")
        time_begin = t[0]
        time_end = t[1]
        overloaded = ("overloaded" in v) and v["overloaded"]
        # Fast enough. Takes about 5 secs. No need for a parallelization.
        stgdev_tio_dlr[stgdev][target_iops] = DstatLogReader(dn, exp_dt, time_begin, time_end, overloaded)

    with open(fn_out, "w") as fo:
      fmt = "%17s %9s %6.0f %1d" \
          " %6.0f %4.0f %9.0f %8.0f %7.0f %6.0f" \
          " %6.3f %6.3f %9.3f %8.3f %8.3f %8.3f" \
          " %8.3f %8.3f %9.3f %8.3f"
      fo.write("%s\n" % Util.BuildHeader(fmt, "exp_dt stg_dev target_iops overloaded" \
          " dsk/xvda:read dsk/xvda:writ dsk/xvdc:read dsk/xvdc:writ dsk/xvde:read dsk/xvde:writ" \
          " io/xvda:read io/xvda:writ io/xvdc:read io/xvdc:writ io/xvde:read io/xvde:writ" \
          " memory_usage:buff memory_usage:cach memory_usage:free memory_usage:used"
          ))
      for stgdev, v in sorted(stgdev_tio_dlr.iteritems()):
        for tio, dlr in sorted(v.iteritems()):
          fo.write((fmt + "\n") % (
            dlr.exp_dt
            , stgdev
            , tio
            , (1 if dlr.overloaded else 0)
            , dlr.GetAvg("dsk/xvda:read")
            , dlr.GetAvg("dsk/xvda:writ")
            , dlr.GetAvg("dsk/xvdc:read")
            , dlr.GetAvg("dsk/xvdc:writ")
            , dlr.GetAvg("dsk/xvde:read")
            , dlr.GetAvg("dsk/xvde:writ")

            , dlr.GetAvg("io/xvda:read")
            , dlr.GetAvg("io/xvda:writ")
            , dlr.GetAvg("io/xvdc:read")
            , dlr.GetAvg("io/xvdc:writ")
            , dlr.GetAvg("io/xvde:read")
            , dlr.GetAvg("io/xvde:writ")

            , dlr.GetAvg("memory_usage:buff") / (1024 *1024)
            , dlr.GetAvg("memory_usage:cach") / (1024 *1024)
            , dlr.GetAvg("memory_usage:free") / (1024 *1024)
            , dlr.GetAvg("memory_usage:used") / (1024 *1024)
            ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out


class DstatLogReader:
  def __init__(self, dn, exp_dt, time_begin, time_end, overloaded):
    self.exp_dt = exp_dt
    self.overloaded = overloaded
    self.exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")
    self.time_begin = time_begin
    self.time_end = time_end

    fn_log_dstat = "%s/dstat/%s.csv" % (dn, exp_dt)
    # Unzip when the file is not there
    if not os.path.exists(fn_log_dstat):
      fn_zipped = "%s.bz2" % fn_log_dstat
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn_log_dstat)
      Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn_log_dstat):
      raise RuntimeError("Unexpected")

    self._Parse(fn_log_dstat)

  def _Parse(self, fn):
    with Cons.MT("Parsing %s ..." % fn):
      header_rows = []
      body_rows = []
      exp_begin_dt_year_str = self.exp_begin_dt.strftime("%y")
      with open(fn, "rb") as f:
        header_detected = False
        reader = csv.reader(f)
        for row in reader:
          if (0 < len(row)) and (row[0] in ["system", "time"]):
            header_rows.append(row)
            header_detected = True
          elif header_detected:
            body_rows.append(BodyRow(row, self.exp_begin_dt, exp_begin_dt_year_str))
        #Cons.P(pprint.pformat(header_rows))

      # Make sure the rows are of the same size
      num_cols = None
      for r in header_rows:
        if num_cols is None:
          num_cols = len(r)
        else:
          if num_cols != len(r):
            raise RuntimeError("Unexpected")
      for r in body_rows:
        if num_cols != r.NumCols():
          raise RuntimeError("Unexpected")

      # Get column headers
      col_names = []
      header_rows_0_prev = None
      for i in range(num_cols):
        if len(header_rows[0][i]) > 0:
          col_names.append("%s:%s" % (header_rows[0][i].replace(" ", "_"), header_rows[1][i].replace(" ", "_")))
          header_rows_0_prev = header_rows[0][i].replace(" ", "_")
        else:
          col_names.append("%s:%s" % (header_rows_0_prev.replace(" ", "_"), header_rows[1][i].replace(" ", "_")))
      #Cons.P(pprint.pformat(col_names))

      # {column_name: idx}
      self.cn_idx = {}
      i = 0
      for cn in col_names:
        self.cn_idx[cn] = i
        i += 1
      #Cons.P(pprint.pformat(self.cn_idx))

      self.body_rows_in_time_range = []
      for b in body_rows:
        if b.TimeInRange(self.time_begin, self.time_end):
          self.body_rows_in_time_range.append(b)
      #Cons.P("%d %d" % (len(body_rows), len(self.body_rows_in_time_range)))
  
    # Key can be one of:
    #   dsk/xvda:read
    #   dsk/xvda:writ
    #   dsk/xvdc:read
    #   dsk/xvdc:writ
    #   io/xvda:read
    #   io/xvda:writ
    #   io/xvdc:read
    #   io/xvdc:writ
    #   memory_usage:buff
    #   memory_usage:cach
    #   memory_usage:free
    #   memory_usage:used
    #   net/total:recv
    #   net/total:send
    #   system:csw
    #   system:int
    #   system:time
    #   total_cpu_usage:hiq
    #   total_cpu_usage:idl
    #   total_cpu_usage:siq
    #   total_cpu_usage:sys
    #   total_cpu_usage:usr
    #   total_cpu_usage:wai
  def GetAvg(self, key):
    if key not in self.cn_idx:
      return 0.0
    v = 0.0
    idx = self.cn_idx[key]
    for b in self.body_rows_in_time_range:
      v += float(b.row[idx])
    return v / len(self.body_rows_in_time_range)


class BodyRow:
  def __init__(self, row, exp_begin_dt, exp_begin_dt_year_str):
    self.row = row
    self.exp_begin_dt = exp_begin_dt
    self.exp_begin_dt_year_str = exp_begin_dt_year_str
    self._CalcRelTime()

  def _CalcRelTime(self):
    # "system:time"
    t = datetime.datetime.strptime((self.exp_begin_dt_year_str + self.row[0]), "%y%d-%m %H:%M:%S")

    self.rel_time_str = None
    if t < self.exp_begin_dt:
      return

    # Convert to relative time
    rel_time = t - self.exp_begin_dt
    totalSeconds = rel_time.seconds
    hours, remainder = divmod(totalSeconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    self.rel_time_str = "%02d:%02d:%02d" % (hours, minutes, seconds)

  def NumCols(self):
    return len(self.row)

  def TimeInRange(self, time_begin, time_end):
    return ((self.rel_time_str is not None) and (time_begin <= self.rel_time_str) and (self.rel_time_str <= time_end))
