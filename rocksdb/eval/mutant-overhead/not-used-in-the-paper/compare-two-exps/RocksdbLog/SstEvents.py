import datetime
import os
import re
import sys
import json

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

from CompInfo import CompInfo
from HowCreated import HowCreated

class SstEvents:
  exp_begin_dt = None

  # {sst_id: file_size}
  sstid_size = {}

  cur_sstsize = 0
  cur_numssts = 0

  # {timestamp: total_size}
  # {timestamp: num_ssts}
  # Time granularity is one second. Changes within a second interval are merged together. It's ok.
  ts_sstsize = {}
  ts_numssts = {}

  # Bidirectional map of SSTable ID and creation time
  #   We assume no two timestamps are identical
  sstid_createts = {}
  createts_sstid = {}

  # Mutant option
  migrate_sstables = None

  @staticmethod
  def Init(exp_begin_dt):
    SstEvents.exp_begin_dt = datetime.datetime.strptime(exp_begin_dt, "%y%m%d-%H%M%S.%f")
    SstEvents.sstid_size = {}
    SstEvents.cur_sstsize = 0
    SstEvents.cur_numssts = 0
    SstEvents.ts_sstsize = {}
    SstEvents.ts_numssts = {}
    SstEvents.sstid_createts = {}
    SstEvents.createts_sstid = {}
    SstEvents.migrate_sstables = None

  # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
  # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
  # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
  # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
  @staticmethod
  def Created(line):
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

    ts1 = SstEvents._GetRelTs(mo.group("ts"))

    SstEvents.sstid_size[sst_id] = sst_size
    SstEvents.cur_sstsize += sst_size
    SstEvents.cur_numssts += 1

    SstEvents.ts_sstsize[ts1] = SstEvents.cur_sstsize
    SstEvents.ts_numssts[ts1] = SstEvents.cur_numssts

    SstEvents.sstid_createts[sst_id] = ts1
    SstEvents.createts_sstid[ts1] = sst_id

    hc = HowCreated.Add(sst_id, j1)
    if SstEvents.migrate_sstables:
      if hc.Reason()[0] == "C":
        CompInfo.AddOutSstInfo(j1)


  @staticmethod
  def Deleted(line):
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

    ts1 = SstEvents._GetRelTs(ts0)
    if sst_id not in SstEvents.sstid_size:
      Cons.P("Interesting: Sst (id %d) deleted without a creation. Ignore." % sst_id)
      return
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
    i = 0
    with open(fn, "w") as fo:
      if i % 40 == 0:
        fo.write(header + "\n")
      i += 1
      ts_prev = datetime.timedelta(0)
      ts_str_prev = "00:00:00.000"
      num_ssts_prev = 0
      total_sst_size_prev = 0
      for ts, num_ssts in sorted(SstEvents.ts_numssts.iteritems()):
        ts_str = _ToStr(ts)
        total_sst_size = SstEvents.ts_sstsize[ts]
        sst_id = "-"
        sst_size = "-"
        job_id = "-"
        creation_reason = "-"
        # Temperature-triggered single-sstable migration
        temp_triggered_migr = "-"
        migr_dirc = "-"
        if ts in SstEvents.createts_sstid:
          sst_id = SstEvents.createts_sstid[ts]
          sst_size = SstEvents.sstid_size[sst_id]
          hc = HowCreated.Get(sst_id)
          job_id = hc.JobId()
          creation_reason = hc.Reason()
          temp_triggered_migr = "T" if CompInfo.TempTriggeredSingleSstMigr(job_id) else "-"
          if SstEvents.migrate_sstables:
            if creation_reason == "C":
              migr_dirc = CompInfo.MigrDirc(job_id, sst_id)

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
