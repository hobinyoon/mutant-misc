import datetime
import os
import re
import sys
import json

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class SstEvents:
  def __init__(self, rocks_log_reader, exp_begin_dt):
    self.rocks_log_reader = rocks_log_reader
    self.exp_begin_dt = datetime.datetime.strptime(exp_begin_dt, "%y%m%d-%H%M%S.%f")
    # {sst_id: file_size}
    self.sstid_size = {}
    self.cur_sstsize = 0
    self.cur_numssts = 0
    # {timestamp: total_size}
    # {timestamp: num_ssts}
    self.ts_sstsize = {}
    self.ts_numssts = {}
    # Creation time to SSTable ID
    #   We assume no two timestamps are identical
    self.createts_sstid = {}


  # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
  # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
  # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
  # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
  def Created(self, line):
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

    ts1 = self._GetRelTs(mo.group("ts"))

    self.sstid_size[sst_id] = sst_size
    self.cur_sstsize += sst_size
    self.cur_numssts += 1

    self.ts_sstsize[ts1] = self.cur_sstsize
    self.ts_numssts[ts1] = self.cur_numssts

    self.createts_sstid[ts1] = sst_id

    hc = self.rocks_log_reader.how_created.Add(sst_id, j1)
    if self.rocks_log_reader.migrate_sstables:
      if hc.Reason()[0] == "C":
        self.rocks_log_reader.comp_info.AddOutSstInfo(j1)


  def Deleted(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    j = mo.group("json")
    try:
      j1 = json.loads(j)
    except ValueError as e:
      Cons.P("%s [%s]" % (e, line))
      sys.exit(1)

    ts0 = mo.group("ts")
    sst_id = int(j1["file_number"])

    ts1 = self._GetRelTs(ts0)
    if sst_id not in self.sstid_size:
      Cons.P("Interesting: Sst (id %d) deleted without a creation. Ignore." % sst_id)
      return
    self.cur_sstsize -= self.sstid_size[sst_id]
    self.cur_numssts -= 1
    self.ts_sstsize[ts1] = self.cur_sstsize
    self.ts_numssts[ts1] = self.cur_numssts


  def _GetRelTs(self, ts0):
    ts = datetime.datetime.strptime(ts0, "%Y/%m/%d-%H:%M:%S.%f")
    ts_rel = ts - self.exp_begin_dt
    return ts_rel


  def Write(self, fn):
    with open(fn, "w") as fo:
      fmt = "%12s %12s %7.3f %4d %4d %7.3f %7.3f" \
          " %4s %9s %4s %1s %1s %1s"
      header = Util.BuildHeader(fmt, "rel_ts_HHMMSS_begin" \
          " rel_ts_HHMMSS_end" \
          " ts_dur" \
          " num_sstables_begin" \
          " num_sstables_end" \
          " sstable_size_sum_in_gb_begin" \
          " sstable_size_sum_in_gb_end" \
          \
          " end_sst_id" \
          " end_sst_size" \
          " end_sst_creation_jobid" \
          " end_sst_creation_reason" \
          " end_sst_temp_triggered_single_migr" \
          " end_sst_migration_direction")

      ts_prev = datetime.timedelta(0)
      ts_str_prev = "00:00:00.000"
      num_ssts_prev = 0
      total_sst_size_prev = 0
      i = 0
      for ts, num_ssts in sorted(self.ts_numssts.iteritems()):
        if i % 40 == 0:
          fo.write(header + "\n")
        i += 1
        ts_str = _ToStr(ts)
        total_sst_size = self.ts_sstsize[ts]
        sst_id = "-"
        sst_size = "-"
        job_id = "-"
        creation_reason = "-"
        # Temperature-triggered single-sstable migration
        temp_triggered_migr = "-"
        migr_dirc = "-"
        if ts in self.createts_sstid:
          sst_id = self.createts_sstid[ts]
          sst_size = self.sstid_size[sst_id]
          hc = self.rocks_log_reader.how_created.Get(sst_id)
          job_id = hc.JobId()
          creation_reason = hc.Reason()

          temp_triggered_migr = "T" if self.rocks_log_reader.comp_info.TempTriggeredSingleSstMigr(job_id) else "-"
          if self.rocks_log_reader.migrate_sstables:
            if creation_reason == "C":
              migr_dirc = self.rocks_log_reader.comp_info.MigrDirc(job_id, sst_id)

        fo.write((fmt + "\n") % (ts_str_prev
          , ts_str
          , (ts.total_seconds() - ts_prev.total_seconds())
          , num_ssts_prev
          , num_ssts
          , (float(total_sst_size_prev) / 1024 / 1024 / 1024)
          , (float(total_sst_size) / 1024 / 1024 / 1024)

          , sst_id
          , sst_size
          , job_id
          , creation_reason
          , temp_triggered_migr
          , migr_dirc
          ))
        ts_str_prev = ts_str
        ts_prev = ts
        num_ssts_prev = num_ssts
        total_sst_size_prev = total_sst_size
    Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))

  def __repr__(self):
    s = []
    for k, v in sorted(vars(self).items()):
      if k == "rocks_log_reader":
        continue
      if isinstance(v, dict):
        s.append("len(%s)=%d" % (k, len(v)))
      else:
        s.append("%s=%s" % (k, v))
    return "<%s>" % " ".join(s)


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
