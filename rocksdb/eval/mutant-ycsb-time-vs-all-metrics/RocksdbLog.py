import datetime
import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf

def GenDataFileForGnuplot(p):
  lr = RocksdbLogReader(p)
  return lr.FnMetricByTime()


class RocksdbLogReader:
  def __init__(self, p):
    self.fn_out = "%s/rocksdb-by-time-%s" % (Conf.GetOutDir(), p.exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.exp_begin_dt = datetime.datetime.strptime(p.exp_dt, "%y%m%d-%H%M%S.%f")
    #Cons.P(self.exp_begin_dt)

    with Cons.MT("Generating rocksdb time-vs-metrics file for plot ..."):
      fn_log_rocksdb = "%s/%s/rocksdb/%s" % (p.dn_base, p.job_id, p.exp_dt)

      if not os.path.exists(fn_log_rocksdb):
        fn_zipped = "%s.bz2" % fn_log_rocksdb
        if not os.path.exists(fn_zipped):
          raise RuntimeError("Unexpected: %s" % fn_log_rocksdb)
        Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
      if not os.path.exists(fn_log_rocksdb):
        raise RuntimeError("Unexpected")
      Cons.P(fn_log_rocksdb)

      # Histogram with 1 second binning
      # {rel_ts: [(file_size, creation_reason)]}
      ts_size = {}
      with open(fn_log_rocksdb) as fo:
        for line in fo:
          #Cons.P(line)
          if "\"event\": \"table_file_creation\"" in line:
            # 2017/12/04-05:01:38.488279 7f460a242700 EVENT_LOG_v1 {"time_micros": 1512363698488254, "cf_name": "usertable", "job": 1, "event":
            # "table_file_creation", "file_number": 2427, "file_size": 129222378, "path_id": 0, "table_properties": {"data_size": 128387602, "index_size":
            # 833929, "filter_size": 0, "raw_key_size": 3383351, "raw_average_key_size": 30, "raw_value_size": 124905240, "raw_average_value_size": 1140,
            # "num_data_blocks": 27392, "num_entries": 109566, "filter_policy_name": "", "reason": kRecovery, "kDeletedKeys": "0", "kMergeOperands": "0"}
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)

            ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
            ts_rel = ts - self.exp_begin_dt

            # Fix the illegal json format
            j = mo.group("json").replace("kFlush", "\"kFlush\"").replace("kCompaction", "\"kCompaction\"").replace("kRecovery", "\"kRecovery\"")
            try:
              j1 = json.loads(j)
            except ValueError as e:
              Cons.P("%s [%s]" % (e, line))
              sys.exit(1)

            # You may be able to use path_id later
            sst_size = int(j1["file_size"])
            creation_reason = j1["table_properties"]["reason"][1:2]
            #Cons.P("%s %d %s" % (ts_rel, sst_size, creation_reason))

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
            ts_size[ts1].append((sst_size, creation_reason))

      fmt = "%8s %2d %9d %-1s"
      with open(self.fn_out, "w") as fo:
        fo.write(Util.BuildHeader(fmt, "rel_ts_HHMMSS num_sstables sum_sst_sizes creation_reason") + "\n")
        for ts, v in sorted(ts_size.iteritems()):
          size = 0
          creation_reason = ""
          for v1 in v:
            size += v1[0]
            creation_reason += v1[1]
          fo.write((fmt + "\n") % (ts, len(v), size, creation_reason))
      Cons.P("Created %s %d" % (self.fn_out, os.path.getsize(self.fn_out)))


  def FnMetricByTime(self):
    return self.fn_out
