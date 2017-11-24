import datetime
import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf

def GenDataFileForGnuplot(dn_log_job, exp_dt):
  lr = RocksdbLogReader(dn_log_job, exp_dt)
  return lr.FnMetricByTime()


class RocksdbLogReader:
  def __init__(self, dn_log_job, exp_dt):
    self.fn_out = "%s/rocksdb-by-time-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")
    #Cons.P(self.exp_begin_dt)

    with Cons.MT("Generating rocksdb time-vs-metrics file for plot ..."):
      fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)

      if not os.path.exists(fn_log_rocksdb):
        fn_zipped = "%s.bz2" % fn_log_rocksdb
        if not os.path.exists(fn_zipped):
          raise RuntimeError("Unexpected: %s" % fn_log_rocksdb)
        Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
      if not os.path.exists(fn_log_rocksdb):
        raise RuntimeError("Unexpected")
      Cons.P(fn_log_rocksdb)

      # Histogram with 1 second binning
      # {rel_ts: [file_size]}
      ts_size = {}
      with open(fn_log_rocksdb) as fo:
        for line in fo:
          #Cons.P(line)
          if "\"event\": \"table_file_creation\"" in line:
            #Cons.P(line)
            # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event": "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779, "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140, "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)

            ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
            ts_rel = ts - self.exp_begin_dt

            # Fix the illegal json format
            j = mo.group("json").replace("kFlush", "\"kFlush\"").replace("kCompaction", "\"kCompaction\"")
            try:
              j1 = json.loads(j)
            except ValueError as e:
              Cons.P("%s [%s]" % (e, line))
              sys.exit(1)

            # You may be able to use path_id later
            sst_size = int(j1["file_size"])
            #Cons.P("%s %d" % (ts_rel, sst_size))

            total_s = ts_rel.total_seconds()
            s = total_s % 60
            total_s -= s
            total_m = total_s / 60
            m = total_m % 60
            total_m -= m
            h = total_m / 60

            ts1 = "%02d:%02d:%02d" % (h, m, s)
            if ts1 not in ts_size:
              ts_size[ts1] = []
            ts_size[ts1].append(sst_size)

      fmt = "%8s %2d %9d"
      with open(self.fn_out, "w") as fo:
        fo.write(Util.BuildHeader(fmt, "rel_ts_HHMMSS num_sstables sum_sst_sizes") + "\n")
        for ts, sizes in sorted(ts_size.iteritems()):
          fo.write((fmt + "\n") % (ts, len(sizes), sum(sizes)))
      Cons.P("Created %s %d" % (self.fn_out, os.path.getsize(self.fn_out)))


  def FnMetricByTime(self):
    return self.fn_out
