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

    SstEvents.SetExpBeginDt(exp_dt)

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

      with open(fn_log_rocksdb) as fo:
        for line in fo:
          #Cons.P(line)

          # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
          # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
          # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
          # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
          if "\"event\": \"table_file_creation\"" in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)

            # Fix the illegal json format
            j = mo.group("json").replace("kFlush", "\"kFlush\"").replace("kCompaction", "\"kCompaction\"").replace("kRecovery", "\"kRecovery\"")
            try:
              j1 = json.loads(j)
            except ValueError as e:
              Cons.P("%s [%s]" % (e, line))
              sys.exit(1)

            sst_size = int(j1["file_size"])
            sst_id = int(j1["file_number"])
            SstEvents.Created(mo.group("ts"), sst_id, sst_size)

          # 2018/01/01-05:33:49.183505 7f97d0ff1700 EVENT_LOG_v1 {"time_micros": 1514784829183496, "job": 6, "event": "table_file_deletion", "file_number": 21}
          elif "\"event\": \"table_file_deletion\"" in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)

            try:
              j1 = json.loads(j)
            except ValueError as e:
              Cons.P("%s [%s]" % (e, line))
              sys.exit(1)

            sst_id = int(j1["file_number"])
            SstEvents.Deleted(mo.group("ts"), sst_id)

      SstEvents.Write(self.fn_out)

  def FnMetricByTime(self):
    return self.fn_out


class SstEvents:
  exp_begin_dt = None

  # Number of new SSTables and their sizes. 1-second binning for a histogram.
  # {rel_ts: [new_sst_file_size]}
  ts_nsfs = {}

  # {sst_id: file_size}
  sstid_size = {}

  cur_sstsize = 0
  cur_numssts = 0

  # {timestamp: total_size}
  # {timestamp: num_ssts}
  # Time granularity is one second. Changes within a second interval are merged together. It's ok.
  ts_sstsize = {}
  ts_numssts = {}

  @staticmethod
  def SetExpBeginDt(exp_begin_dt):
    SstEvents.exp_begin_dt = datetime.datetime.strptime(exp_begin_dt, "%y%m%d-%H%M%S.%f")

  @staticmethod
  def Created(ts0, sst_id, sst_size):
    ts1 = SstEvents._GetRelTs(ts0)
    if ts1 not in SstEvents.ts_nsfs:
      SstEvents.ts_nsfs[ts1] = []
    SstEvents.ts_nsfs[ts1].append(sst_size)

    SstEvents.sstid_size[sst_id] = sst_size
    SstEvents.cur_sstsize += sst_size
    SstEvents.cur_numssts += 1

    SstEvents.ts_sstsize[ts1] = SstEvents.cur_sstsize
    SstEvents.ts_numssts[ts1] = SstEvents.cur_numssts

  @staticmethod
  def Deleted(ts0, sst_id):
    ts1 = SstEvents._GetRelTs(ts0)
    SstEvents.cur_sstsize -= SstEvents.sstid_size[sst_id]
    SstEvents.cur_numssts -= 1
    SstEvents.ts_sstsize[ts1] = SstEvents.cur_sstsize
    SstEvents.ts_numssts[ts1] = SstEvents.cur_numssts

  @staticmethod
  def _GetRelTs(ts0):
    ts = datetime.datetime.strptime(ts0, "%Y/%m/%d-%H:%M:%S.%f")
    ts_rel = ts - SstEvents.exp_begin_dt
    return ts_rel

  @staticmethod
  def Write(fn):
    fmt = "%12s %4d %12d %2d %10d"
    with open(fn, "w") as fo:
      fo.write(Util.BuildHeader(fmt, "rel_ts_HHMMSS" \
        " num_sstables" \
        " sstable_size_sum" \
        " num_new_sstables" \
        " new_sst_sizes") + "\n")
      for ts, num_ssts in sorted(SstEvents.ts_numssts.iteritems()):
        fo.write((fmt + "\n") % (_ToStr(ts)
          , num_ssts
          , SstEvents.ts_sstsize[ts]
          , (len(SstEvents.ts_nsfs[ts]) if ts in SstEvents.ts_nsfs else 0)
          , (sum(SstEvents.ts_nsfs[ts]) if ts in SstEvents.ts_nsfs else 0)
          ))
    Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))


def _ToStr(td):
  total_s = td.total_seconds()
  frac = str(total_s % 1)[2:5]
  s = total_s % 60
  total_s -= s
  total_m = total_s / 60
  m = total_m % 60
  total_m -= m
  h = total_m / 60
  return "%02d:%02d:%02d.%s" % (h, m, s, frac)
