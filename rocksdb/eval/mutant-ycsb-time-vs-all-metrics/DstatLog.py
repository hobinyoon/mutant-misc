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
_header_idx = None
_num_stg_devs = 0
_body_rows = None

_exp_begin_dt = None

# Generate a formatted output file for gnuplot. The csv file has headers that's not ideal for gnuplot.
def GenDataFileForGnuplot(p):
  fn_out = "%s/dstat-%s" % (Conf.GetOutDir(), p.exp_dt)
  if os.path.isfile(fn_out):
    return fn_out

  global _exp_begin_dt
  _exp_begin_dt = datetime.datetime.strptime(p.exp_dt, "%y%m%d-%H%M%S.%f")
  #Cons.P(_exp_begin_dt)

  with Cons.MT("Generating dstat data file for plot ..."):
    global _header_idx
    global _body_rows
    _header_idx = None
    _body_rows = None

    fn_log_dstat = "%s/%s/dstat/%s.csv" % (p.dn_base, p.job_id, p.exp_dt)
    # Unzip when the file is not there
    if not os.path.exists(fn_log_dstat):
      fn_zipped = "%s.bz2" % fn_log_dstat
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn_log_dstat)
      Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn_log_dstat):
      raise RuntimeError("Unexpected")

    _Parse(fn_log_dstat)

    # For read and write
    fmt = " ".join(["%9.0f"] * 2 * _num_stg_devs + ["%6.1f"] * 2 * _num_stg_devs)

    fmt += " %8.0f %8.0f %8.0f %8.0f" \
        " %3.0f %3.0f" \
        " %3.0f %3.0f %11s" \
        " %3.1f %6.2f %3.1f %6.2f %6.2f %6.3f"

    header = Util.BuildHeader(fmt, " ".join(k for k, v in sorted(_header_idx.iteritems())))
    #Cons.P(header)
    with open(fn_out, "w") as fo:
      i = 0
      for r in _body_rows:
        if not r.TimeValid():
          continue
        if i % 50 == 0:
          fo.write("%s\n" % header)
        i += 1
        fo.write((fmt + "\n") % tuple(r.Prepared()))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out


class BodyRow:
  def __init__(self, r):
    self.raw_row = r

  def NumCols(self):
    return len(self.raw_row)

  # Sort the data in the header order and convert strings to numbers
  def PrepareData(self):
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


def _Parse(fn):
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
    global _header_idx
    _header_idx = {}
    header_rows_0_prev = None
    for i in range(num_cols):
      if len(header_rows[0][i]) > 0:
        #Cons.P("%s, %s" % (header_rows[0][i], header_rows[1][i]))
        _header_idx["%s:%s" % (header_rows[0][i].replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
        header_rows_0_prev = header_rows[0][i].replace(" ", "_")
      else:
        #Cons.P("%s, %s" % (header_rows_0_prev, header_rows[1][i]))
        _header_idx["%s:%s" % (header_rows_0_prev.replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
    #Cons.P(pprint.pformat(_header_idx))

    # Count the number of storage devices
    num_stg_devs = 0
    for k, v in _header_idx.iteritems():
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
