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
    self.cur_sstsize = [0, 0]
    self.cur_numssts = [0, 0]
    # {timestamp: [total_fast_storage_size, total_slow_storage_size]}
    # {timestamp: [num_ssts_in_fast_storage, num_ssts_in_slow_storage]}
    self.ts_sstsize = {}
    self.ts_numssts = {}

    # Creation time to SSTable ID and deletion time to one
    #   We assume no two timestamps are identical
    self.createts_sstid = {}
    self.deletets_sstid = {}


  # 2018/02/27-16:49:17.959334 7ff0ed2b2700 EVENT_LOG_v1 {"time_micros": 1519750157959324, "mutant_sst_opened": {"file_number": 2274, "file_size":
  # 10950641, "path_id": 0, "level": 1}}
  def Created1(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)

    try:
      j1 = json.loads(mo.group("json"))
    except ValueError as e:
      Cons.P("%s [%s]" % (e, line))
      sys.exit(1)

    j2 = j1["mutant_sst_opened"]

    sst_size = int(j2["file_size"])
    sst_id = int(j2["file_number"])
    path_id = int(j2["path_id"])
    level = int(j2["level"])

    ts1 = self._GetRelTs(mo.group("ts"))

    self.cur_sstsize[path_id] += sst_size
    self.cur_numssts[path_id] += 1

    self.ts_sstsize[ts1] = list(self.cur_sstsize)
    self.ts_numssts[ts1] = list(self.cur_numssts)

    self.createts_sstid[ts1] = sst_id

    self.rocks_log_reader.sst_info.Add(sst_id, j1)
  
  
  # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
  # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
  # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
  # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
  def Created2(self, line):
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

    sst_id = int(j1["file_number"])

    si = self.rocks_log_reader.sst_info.Update(sst_id, j1)
    if self.rocks_log_reader.migrate_sstables:
      if si.Reason()[0] == "C":
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
    si = self.rocks_log_reader.sst_info.Get(sst_id)
    if si is None:
      # This happens when RocksDB loads existing database. It doesn't log anything.
      Cons.P("Interesting: Sst (id %d) deleted without a creation. Ignore." % sst_id)
      return
    path_id = si.PathId()
    self.cur_sstsize[path_id] -= si.Size()
    self.cur_numssts[path_id] -= 1
    self.ts_sstsize[ts1] = list(self.cur_sstsize)
    self.ts_numssts[ts1] = list(self.cur_numssts)

    self.deletets_sstid[ts1] = sst_id


  def _GetRelTs(self, ts0):
    ts = datetime.datetime.strptime(ts0, "%Y/%m/%d-%H:%M:%S.%f")
    ts_rel = ts - self.exp_begin_dt
    return ts_rel


  def GetStgTimeSize(self, time_max):
    #fmt = "%15s %5.3f %11.9f %5.3f %11.9f"
    #Cons.P(Util.BuildHeader(fmt, "time_end" \
    #    " total_fast_sst_size_end fast_sst_time_size_gb_month" \
    #    " total_slow_sst_size_end slow_sst_time_size_gb_month" \
    #    ))

    ts_prev = datetime.timedelta()
    # Fast and slow storage
    total_sst_size_prev = [0, 0]
    time_size = [0.0, 0.0]
    time_size_gb_month = [0.0, 0.0]

    done = False
    for ts, total_sst_size in sorted(self.ts_sstsize.iteritems()):
      if done:
        break

      if time_max and (time_max <= ts):
        ts = time_max
        done = True

      time_dur = ts.total_seconds() - ts_prev.total_seconds()
      time_size[0] += (time_dur * total_sst_size_prev[0])
      time_size[1] += (time_dur * total_sst_size_prev[1])

      time_size_gb_month = [
          float(time_size[0]) / 1024 / 1024 / 1024 / (3600 * 24 * 365.25 / 12)
          , float(time_size[1]) / 1024 / 1024 / 1024 / (3600 * 24 * 365.25 / 12)
          ]
      #Cons.P(fmt % (ts
      #  , float(total_sst_size[0]) / 1024 / 1024 / 1024, time_size_gb_month[0]
      #  , float(total_sst_size[1]) / 1024 / 1024 / 1024, time_size_gb_month[1]
      #  ))
      ts_prev = ts
      total_sst_size_prev = list(total_sst_size)

    return time_size_gb_month


  def Write(self, fn):
    with open(fn, "w") as fo:
      fmt = "%12s %4d %4d %7.3f %7.3f %8.6f" \
          " %4s %9s %1s %4s %1s %1s %1s" \
          " %8.6f %8.6f %8.6f"
      header = Util.BuildHeader(fmt, "rel_ts_HHMMSS" \
          " num_fast_sstables" \
          " num_slow_sstables" \
          " fast_sstable_size_sum_in_gb" \
          " slow_sstable_size_sum_in_gb" \
          " current_stg_cost_in_gb_month" \
          \
          " sst_id" \
          " sst_size" \
          " sst_path_id" \
          " sst_creation_jobid" \
          " sst_creation_reason" \
          " sst_temp_triggered_single_migr" \
          " sst_migration_direction" \
          " cur_stg_cost_leveled_split_01" \
          " cur_stg_cost_leveled_split_12" \
          " cur_stg_cost_leveled_split_23" \
          )

      stg_unit_price = self.rocks_log_reader.stg_cost.GetUnitPrice()
      ts_prev = datetime.timedelta(0)
      ts_str_prev = "00:00:00.000"
      num_ssts_prev = [0, 0]
      total_sst_size_prev = [0, 0]
      cur_sst_size_by_levels = {0:0, 1:0, 2:0, 3:0}
      cur_stg_cost_by_level01_prev = 0
      cur_stg_cost_by_level12_prev = 0
      cur_stg_cost_by_level23_prev = 0
      i = 0
      for ts, num_ssts in sorted(self.ts_numssts.iteritems()):
        if i % 40 == 0:
          fo.write(header + "\n")
        i += 1
        ts_str = _ToStr(ts)
        total_sst_size = self.ts_sstsize[ts]
        sst_id = "-"
        sst_size = "-"
        path_id = "-"
        job_id = "-"
        creation_reason = "-"
        # Temperature-triggered single-sstable migration
        temp_triggered_migr = "-"
        migr_dirc = "-"
        if ts in self.createts_sstid:
          sst_id = self.createts_sstid[ts]
          si = self.rocks_log_reader.sst_info.Get(sst_id)
          sst_size = si.Size()
          path_id = si.PathId()
          if si.JobId() is not None:
            job_id = si.JobId()
          if si.Reason() is not None:
            creation_reason = si.Reason()

          cur_sst_size_by_levels[si.Level()] += sst_size

          temp_triggered_migr = "T" if self.rocks_log_reader.comp_info.TempTriggeredSingleSstMigr(job_id) else "-"
          if self.rocks_log_reader.migrate_sstables:
            if creation_reason == "C":
              migr_dirc = self.rocks_log_reader.comp_info.MigrDirc(job_id, sst_id)

        if ts in self.deletets_sstid:
          sst_id = self.deletets_sstid[ts]
          si = self.rocks_log_reader.sst_info.Get(sst_id)
          sst_size = si.Size()
          cur_sst_size_by_levels[si.Level()] -= sst_size

        total_stg_size_prev = total_sst_size_prev[0] + total_sst_size_prev[1]
        total_stg_size = total_sst_size[0] + total_sst_size[1]
        stg_cost_prev = (float(total_sst_size_prev[0]) * stg_unit_price[0] + float(total_sst_size_prev[1]) * stg_unit_price[1]) \
            / total_stg_size_prev if total_stg_size_prev != 0 else 0
        stg_cost = (float(total_sst_size[0]) * stg_unit_price[0] + float(total_sst_size[1]) * stg_unit_price[1]) / total_stg_size if total_stg_size != 0 else 0

        total_stg_size = cur_sst_size_by_levels[0] + cur_sst_size_by_levels[1] + cur_sst_size_by_levels[2] + cur_sst_size_by_levels[3]
        cur_stg_cost_by_level01 = \
            (cur_sst_size_by_levels[0] * stg_unit_price[0]
                + cur_sst_size_by_levels[1] * stg_unit_price[1]
                + cur_sst_size_by_levels[2] * stg_unit_price[1]
                + cur_sst_size_by_levels[3] * stg_unit_price[1]) \
            / total_stg_size
        cur_stg_cost_by_level12 = \
            (cur_sst_size_by_levels[0] * stg_unit_price[0]
                + cur_sst_size_by_levels[1] * stg_unit_price[0]
                + cur_sst_size_by_levels[2] * stg_unit_price[1]
                + cur_sst_size_by_levels[3] * stg_unit_price[1]) \
            / total_stg_size
        cur_stg_cost_by_level23 = \
            (cur_sst_size_by_levels[0] * stg_unit_price[0]
                + cur_sst_size_by_levels[1] * stg_unit_price[0]
                + cur_sst_size_by_levels[2] * stg_unit_price[0]
                + cur_sst_size_by_levels[3] * stg_unit_price[1]) \
            / total_stg_size

        fo.write((fmt + "\n") % (ts_str
          , num_ssts_prev[0]
          , num_ssts_prev[1]
          , (float(total_sst_size_prev[0]) / 1024 / 1024 / 1024)
          , (float(total_sst_size_prev[1]) / 1024 / 1024 / 1024)
          , stg_cost_prev

          , "-" # sst_id
          , "-" # sst_size
          , "-" # path_id
          , "-" # job_id
          , "-" # creation_reason
          , "-" # temp_triggered_migr
          , "-" # migr_dirc

          , cur_stg_cost_by_level01_prev
          , cur_stg_cost_by_level12_prev
          , cur_stg_cost_by_level23_prev
          ))

        fo.write((fmt + "\n") % (ts_str
          , num_ssts[0]
          , num_ssts[1]
          , (float(total_sst_size[0]) / 1024 / 1024 / 1024)
          , (float(total_sst_size[1]) / 1024 / 1024 / 1024)
          , stg_cost

          , sst_id
          , sst_size
          , path_id
          , job_id
          , creation_reason
          , temp_triggered_migr
          , migr_dirc

          , cur_stg_cost_by_level01
          , cur_stg_cost_by_level12
          , cur_stg_cost_by_level23
          ))
        ts_str_prev = ts_str
        ts_prev = ts
        num_ssts_prev = list(num_ssts)
        total_sst_size_prev = list(total_sst_size)

        cur_stg_cost_by_level01_prev = cur_stg_cost_by_level01
        cur_stg_cost_by_level12_prev = cur_stg_cost_by_level12
        cur_stg_cost_by_level23_prev = cur_stg_cost_by_level23

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
