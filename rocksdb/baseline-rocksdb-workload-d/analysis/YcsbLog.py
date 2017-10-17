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
  return lr.FnMetricByTime()


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

      fmt = "%5d %9.2f" \
          " %6d %8.2f %3d %6d" \
          " %6d %6d %6d %6d" \
          " %6d %8.2f %3d %6d" \
          " %6d %6d %6d %6d"
      Cons.P(Util.BuildHeader(fmt, "rel_time_sec db_iops" \
          " read_cnt read_lat_avg read_lat_min read_lat_max" \
          " read_lat_90p read_lat_99p read_lat_99.9p read_lat_99.99p" \
          " write_cnt write_lat_avg write_lat_min write_lat_max" \
          " write_lat_90p write_lat_99p write_lat_99.9p write_lat_99.99p" \
          ))
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
            Cons.P(fmt % (
              int(mo.group("rel_time")), float(mo.group("db_iops"))
              , int(mo.group("r_cnt")) , float(mo.group("r_avg")) , int(mo.group("r_min")) , int(mo.group("r_max"))
              , int(mo.group("r_90")) , int(mo.group("r_99")) , int(mo.group("r_999")) , int(mo.group("r_9999"))
              , int(mo.group("w_cnt")) , float(mo.group("w_avg")) , int(mo.group("w_min")) , int(mo.group("w_max"))
              , int(mo.group("w_90")) , int(mo.group("w_99")) , int(mo.group("w_999")) , int(mo.group("w_9999"))
              ))
          else:
            #Cons.P(line)
            pass

      sys.exit(1)

      # TODO: get the options at the end of the file
      # params
      # run






      self.header_idx = None

      global _body_rows
      _body_rows = None


      _Parse(fn_log_ycsb)

      # For read and write
      fmt = " ".join(["%9.0f"] * 2 * _num_stg_devs + ["%6.1f"] * 2 * _num_stg_devs)

      fmt += " %8.0f %8.0f %8.0f %8.0f" \
          " %3.0f %3.0f" \
          " %3.0f %3.0f %11s" \
          " %3.1f %6.2f %3.1f %6.2f %6.2f %6.3f"

      header = Util.BuildHeader(fmt, " ".join(k for k, v in sorted(self.header_idx.iteritems())))
      #Cons.P(header)
      with open(self.fn_out, "w") as fo:
        i = 0
        for r in _body_rows:
          if not r.TimeValid():
            continue
          if i % 50 == 0:
            fo.write("%s\n" % header)
          i += 1
          fo.write((fmt + "\n") % tuple(r.Prepared()))
      Cons.P("Created %s %d" % (self.fn_out, os.path.getsize(self.fn_out)))

  def _Parse(self, fn):
    with Cons.MT("Parsing %s ..." % fn):
      header_rows = []
      global _body_rows
      _body_rows = []
      with open(fn, "rb") as f:
        header_detected = False
        reader = csv.reader(f)
        for row in reader:
          if (0 < len(row)) and (row[0] in ["system", "time"]):
            header_rows.append(row)
            header_detected = True
          elif header_detected:
            _body_rows.append(BodyRow(row))
        #Cons.P(pprint.pformat(header_rows))

      # Make sure the rows are all the same size
      num_cols = None
      for r in header_rows:
        if num_cols is None:
          num_cols = len(r)
        else:
          if num_cols != len(r):
            raise RuntimeError("Unexpected")

      for r in _body_rows:
        if num_cols != r.NumCols():
          raise RuntimeError("Unexpected")

      # Get column headers
      self.header_idx = {}
      header_rows_0_prev = None
      for i in range(num_cols):
        if len(header_rows[0][i]) > 0:
          #Cons.P("%s, %s" % (header_rows[0][i], header_rows[1][i]))
          self.header_idx["%s:%s" % (header_rows[0][i].replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
          header_rows_0_prev = header_rows[0][i].replace(" ", "_")
        else:
          #Cons.P("%s, %s" % (header_rows_0_prev, header_rows[1][i]))
          self.header_idx["%s:%s" % (header_rows_0_prev.replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
      #Cons.P(pprint.pformat(self.header_idx))

      # Count the number of storage devices
      num_stg_devs = 0
      for k, v in self.header_idx.iteritems():
        #Cons.P("%s %s" % (k, v))
        mo = re.match(r"dsk/xvd\w:read", k)
        if mo is not None:
          num_stg_devs += 1
      global _num_stg_devs
      _num_stg_devs = num_stg_devs
      Cons.P("%d storage devices" % num_stg_devs)

      # Sort the data in the header order and convert strings to numbers
      for b in _body_rows:
        b.PrepareData()


class BodyRow:
  def __init__(self, r):
    self.raw_row = r

  def NumCols(self):
    return len(self.raw_row)

  # Sort the data in the header order and convert strings to numbers
  def PrepareData(self):
    # TODO: _exp_begin_dt
    simulation_time_begin_year = _exp_begin_dt.strftime("%y")

    self.row = []
    for h, i in sorted(_header_idx.iteritems()):
      if h.startswith("dsk/xvd") \
          or h.startswith("io/xvd") \
          or h.startswith("total_cpu_usage:"):
            self.row.append(float(self.raw_row[i]))
      elif h.startswith("system:time"):
        # It doesn't have year. Use simulation_time_begin_year.
        # 27-12 15:34:18
        # 01234567890123
        simulation_time = datetime.datetime.strptime((simulation_time_begin_year + self.raw_row[i]), "%y%d-%m %H:%M:%S")

        if simulation_time < _exp_begin_dt:
          self.time_valid = False
          continue
        self.time_valid = True

        # Convert to relative time
        rel = simulation_time - _exp_begin_dt
        totalSeconds = rel.seconds
        hours, remainder = divmod(totalSeconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        r1 = "%s:%s:%s" % (hours, minutes, seconds)
        self.row.append(r1)

      elif h.startswith("memory_usage:") \
          or h.startswith("net/total:") \
          or h.startswith("system:"):
        self.row.append(float(self.raw_row[i]) / 1024.0)
      else:
        self.row.append(self.raw_row[i])

  def TimeValid(self):
    return self.time_valid

  def Prepared(self):
    return self.row
