import csv
import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


def GetPlotFn(fn_ycsb_log):
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb_log)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")

  dn_log_job = "%s/%s" % (dn_log, job_id)
  lr = DstatLogReader(dn_log_job, exp_dt)
  return (lr.OutFn(), lr.NumStgDevs())


def GetPlotFn1(dn_log_job, exp_dt):
  lr = DstatLogReader(dn_log_job, exp_dt)
  return (lr.OutFn(), lr.NumStgDevs())


# Generate a formatted output file for gnuplot. The csv file has headers that's not ideal for gnuplot.
class DstatLogReader:
  def __init__(self, dn_log_job, exp_dt):
    self.fn_out = "%s/dstat-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")
    #Cons.P(self.exp_begin_dt)

    with Cons.MT("Generating dstat data file for plot ..."):
      self.header_idx = {}
      self.body_rows = []
      self.num_stg_devs = 0

      fn_log_dstat = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)
      # Unzip when the file is not there
      if not os.path.exists(fn_log_dstat):
        fn_zipped = "%s.bz2" % fn_log_dstat
        if not os.path.exists(fn_zipped):
          raise RuntimeError("Unexpected: %s" % fn_log_dstat)
        Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
      if not os.path.exists(fn_log_dstat):
        raise RuntimeError("Unexpected")

      self._Parse(fn_log_dstat)

      # For read and write
      fmt = " ".join(["%9.0f"] * 2 * self.num_stg_devs + ["%6.1f"] * 2 * self.num_stg_devs)

      fmt += " %8.0f %8.0f %8.0f %8.0f" \
          " %3.0f %3.0f" \
          " %3.0f %3.0f %11s" \
          " %3.1f %6.2f %3.1f %6.2f %6.2f %6.3f"

      header = Util.BuildHeader(fmt, " ".join(k for k, v in sorted(self.header_idx.iteritems())))
      #Cons.P(header)
      with open(self.fn_out, "w") as fo:
        i = 0
        for r in self.body_rows:
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
      with open(fn, "rb") as f:
        header_detected = False
        reader = csv.reader(f)
        for row in reader:
          if (0 < len(row)) and (row[0] in ["system", "time"]):
            header_rows.append(row)
            header_detected = True
          elif header_detected:
            self.body_rows.append(BodyRow(self, row))
        #Cons.P(pprint.pformat(header_rows))

      # Make sure the rows are all the same size
      num_cols = None
      for r in header_rows:
        if num_cols is None:
          num_cols = len(r)
        else:
          if num_cols != len(r):
            raise RuntimeError("Unexpected")

      for r in self.body_rows:
        if num_cols != r.NumCols():
          raise RuntimeError("Unexpected")

      # Get column headers
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
      for k, v in self.header_idx.iteritems():
        #Cons.P("%s %s" % (k, v))
        mo = re.match(r"dsk/xvd\w:read", k)
        if mo is not None:
          self.num_stg_devs += 1
      Cons.P("%d storage devices" % self.num_stg_devs)

      # Sort the data in the header order and convert strings to numbers
      for b in self.body_rows:
        b.PrepareData()

  def OutFn(self):
    return self.fn_out

  def NumStgDevs(self):
    cols = []
    with open(self.fn_out) as fo:
      for line in fo:
        if not line.startswith("#"):
          break
        line = line.strip()
        tokens = re.split(" +", line)
        if 2 <= len(tokens):
          header_detected = True
          for i in range(1, len(tokens)):
            if tokens[i] != str(i):
              header_detected = False
              break
          if header_detected:
            break
        for i in range(1, len(tokens)):
          cols.append(tokens[i])
    #cols.sort()

    cnt = 0
    for c in cols:
      if c.startswith("dsk/xvd"):
        cnt += 1

    if cnt % 2 != 0:
      raise RuntimeError("Unexpected: %d" % cnt)
    return cnt / 2


class BodyRow:
  def __init__(self, dstat_log_reader, r):
    self.dstat_log_reader = dstat_log_reader
    self.raw_row = r

  def NumCols(self):
    return len(self.raw_row)

  # Sort the data in the header order and convert strings to numbers
  def PrepareData(self):
    simulation_time_begin_year = self.dstat_log_reader.exp_begin_dt.strftime("%y")

    self.row = []
    for h, i in sorted(self.dstat_log_reader.header_idx.iteritems()):
      if h.startswith("dsk/xvd") \
          or h.startswith("io/xvd") \
          or h.startswith("total_cpu_usage:"):
            self.row.append(float(self.raw_row[i]))
      elif h.startswith("system:time"):
        # It doesn't have year. Use simulation_time_begin_year.
        # 27-12 15:34:18
        # 01234567890123
        simulation_time = datetime.datetime.strptime((simulation_time_begin_year + self.raw_row[i]), "%y%d-%m %H:%M:%S")

        if simulation_time < self.dstat_log_reader.exp_begin_dt:
          self.time_valid = False
          continue
        self.time_valid = True

        # Convert to relative time
        rel = simulation_time - self.dstat_log_reader.exp_begin_dt
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
