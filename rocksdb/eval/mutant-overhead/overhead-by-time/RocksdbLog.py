import datetime
import json
import os
import pprint
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

    # These classes are not thread-safe. Fine for now.
    SstEvents.Init(exp_dt)
    HowCreated.Init()
    CompInfo.Init()

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

          # 2018/01/05-08:10:30.085011 7f40083d8700   migrate_sstables: 0
          if "   migrate_sstables: " in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   migrate_sstables: (?P<v>\d).*", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)
            self.migrate_sstables = (mo.group("v") == "1")
            SstEvents.migrate_sstables = self.migrate_sstables

          # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
          # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
          # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
          # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
          elif "\"event\": \"table_file_creation\"" in line:
            SstEvents.Created(line)

          # 2018/01/01-05:33:49.183505 7f97d0ff1700 EVENT_LOG_v1 {"time_micros": 1514784829183496, "job": 6, "event": "table_file_deletion", "file_number": 21}
          elif "\"event\": \"table_file_deletion\"" in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)
            j = mo.group("json")
            try:
              j1 = json.loads(j)
            except ValueError as e:
              Cons.P("%s [%s]" % (e, line))
              sys.exit(1)

            sst_id = int(j1["file_number"])
            SstEvents.Deleted(mo.group("ts"), sst_id)

          # Figure out how an SSTable is created
          # (a) start building CompInfo
          # 2018/01/05-08:40:21.078219 7fd13ffff700 EVENT_LOG_v1 {"time_micros": 1515141621078214, "mutant_sst_compaction_migration": {"in_sst": "(sst_id=16
          # temp=57.345 level=0 path_id=0 size=258423184 age=30) (sst_id=13 temp=3738.166 level=0 path_id=1 size=118885 age=440)", "out_sst_path_id": 1,
          # "temp_triggered_single_sst_compaction": 1}}
          elif "mutant_sst_compaction_migration" in line:
            if not self.migrate_sstables:
              continue
            CompInfo.Add(line)

          # (b) Assign job_id to CompInfo
          # We parse this just because there are multiple files_L0 and json would probably not be able to parse it
          # 2018/01/05-08:40:21.078303 7fd13ffff700 EVENT_LOG_v1 {"time_micros": 1515141621078294, "job": 5, "event": "compaction_started", "files_L0": [16,
          # 13], "files_L0": [16, 13], "score": 0, "input_data_size": 517084138}
          elif "compaction_started" in line:
            if not self.migrate_sstables:
              continue
            CompInfo.AssociateJobId(line)

          # (c) Assign out_sst_info to CompInfo using job_id. It is done when parsing table_file_creation above.

      CompInfo.CalcMigrDirections()
      SstEvents.Write(self.fn_out)

  def FnMetricByTime(self):
    return self.fn_out


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

    if SstEvents.migrate_sstables:
      HowCreated.Add(sst_id, j1)

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
    fmt = "%12s %12s %7.3f %4d %4d %12d %4s %4s %1s %2s %1s"
    with open(fn, "w") as fo:
      fo.write(Util.BuildHeader(fmt, "rel_ts_HHMMSS_begin" \
        " rel_ts_HHMMSS_end" \
        " ts_dur" \
        " num_sstables_begin" \
        " num_sstables_end" \
        " sstable_size_sum_end" \
        " end_sst_id" \
        " end_sst_creation_jobid" \
        " end_sst_creation_reason" \
        " end_sst_migration_type" \
        " end_sst_migration_direction") + "\n")
      ts_prev = datetime.timedelta(0)
      ts_str_prev = "00:00:00.000"
      num_ssts_prev = 0
      total_sst_size_prev = 0
      for ts, num_ssts in sorted(SstEvents.ts_numssts.iteritems()):
        ts_str = _ToStr(ts)
        sst_id = "-"
        job_id = "-"
        creation_reason = "-"
        migr_type = "-"
        migr_direction = "-"
        if SstEvents.migrate_sstables:
          if ts in SstEvents.createts_sstid:
            sst_id = SstEvents.createts_sstid[ts]
            hc = HowCreated.Get(sst_id)
            job_id = hc.JobId()
            creation_reason = hc.Reason()
            if creation_reason == "C":
              (migr_type, migr_direction) = CompInfo.MigrType(job_id, sst_id)

        fo.write((fmt + "\n") % (ts_str_prev
          , ts_str
          , (ts.total_seconds() - ts_prev.total_seconds())
          , num_ssts_prev
          , num_ssts
          , total_sst_size_prev
          , sst_id
          , job_id
          , creation_reason
          , migr_type
          , migr_direction
          ))
        ts_str_prev = ts_str
        ts_prev = ts
        num_ssts_prev = num_ssts
        total_sst_size_prev = SstEvents.ts_sstsize[ts]
    Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))


# How an SSTable was created
class HowCreated:
  sstid_howcreated = {}

  @staticmethod
  def Init():
    HowCreated.sstid_howcreated = {}

  @staticmethod
  def Add(sst_id, j1):
    HowCreated.sstid_howcreated[sst_id] = HowCreated(j1)

  def __init__(self, j1):
    self.sst_id = int(j1["file_number"])
    self.path_id = int(j1["path_id"])
    self.sst_size = int(j1["file_size"])

    # (F)flush, (C)compaction, (M)migration.
    reason = j1["table_properties"]["reason"]
    if reason == "kFlush":
      self.reason = "F"
    elif reason == "kRecovery":
      self.reason = "R"
    elif reason == "kCompaction":
      self.reason = "C"
    else:
      raise RuntimeError("Unexpected: %s" % reason)

    self.job_id = int(j1["job"])
    if self.reason == "C":
      self.comp_info = CompInfo.Get(self.job_id)
      self.comp_info.AddOutSstId(self.sst_id)
    else:
      self.comp_info = None

  def __repr__(self):
    return " ".join("%s=%s" % item for item in sorted(vars(self).items()))

  @staticmethod
  def Get(sst_id):
    return HowCreated.sstid_howcreated[sst_id]

  def Size(self):
    return self.sst_size

  def PathId(self):
    return self.path_id

  def Reason(self):
    return self.reason

  def JobId(self):
    return self.job_id


class CompInfo:
  jobid_compinfo = {}
  insstids_compinfo = {}
  insstid_compinfo = {}

  @staticmethod
  def Init():
    CompInfo.jobid_compinfo = {}
    CompInfo.insstids_compinfo = {}
    CompInfo.insstid_compinfo = {}

  @staticmethod
  def Add(line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    j = mo.group("json")
    try:
      j1 = json.loads(j)
    except ValueError as e:
      Cons.P("%s [%s]" % (e, line))
      sys.exit(1)

    # "in_sst": "(sst_id=61 temp=-1.000 level=0 path_id=0 size=258426536 age=0) (sst_id=51 temp=1621.734 level=0 path_id=0 size=67554476 age=373) (sst_id=52
    # temp=1595.033 level=0 path_id=0 size=67554678 age=372) (sst_id=53 temp=1545.246 level=0 path_id=0 size=55755263 age=371)"
    ci = CompInfo(j1)
    #Cons.P(ci)
    CompInfo.insstids_compinfo[ci.in_sstid_str] = ci
    for sst_id in ci.in_sst_ids:
      CompInfo.insstid_compinfo[sst_id] = ci

  @staticmethod
  def AssociateJobId(line):
    # Make sure values with duplicated keys such as files_L0 are the same.
    #   From level 0 to level 9. Should be enough.
    #     You can't start from 0 and stop when it stops. Some starts with 1 skipping 0.
    for i in range(10):
      k = "files_L%d" % i
      v = None
      for mo in re.finditer((r"%s\": \[" % k), line):
        mo1 = re.match(r"(?P<sst_ids>(\d| |,|)+)\].*", line[mo.end():])
        v1 = mo1.group("sst_ids")
        #Cons.P(v1)
        if v is None:
          v = v1
        else:
          if v != v1:
            raise RuntimeError("Unexpected: [%s] [%s]" % (v, v1))

    # Find str_in_sst_ids and job_id, and match them
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    j = mo.group("json")
    try:
      #Cons.P(line)
      j1 = json.loads(j)
    except ValueError as e:
      Cons.P("%s [%s]" % (e, line))
      sys.exit(1)

    # TODO: Exact match is supposed to be done here. Was going to used the merged sstable ID string.
    #   But some grandparent SSTables were missing.
    #     While fixing the error, work with the old ones by doing an inclusion test instead.
    in_sst_ids = set()
    for i in range(10):
      k = "files_L%d" % i
      if k not in j1:
        continue
      #Cons.P(j1[k])
      for sst_id in j1[k]:
        in_sst_ids.add(sst_id)

    job_id = int(j1["job"])
    job_id_set = False
    #Cons.P("%s %s %d" % (line, in_sst_ids, len(CompInfo.insstids_compinfo)))
    for k, ci in CompInfo.insstids_compinfo.iteritems():
      #Cons.P("  %s" % ci.in_sst_ids)
      if ci.Included(in_sst_ids):
        ci.job_id = job_id
        CompInfo.jobid_compinfo[job_id] = ci
        job_id_set = True
        break
    if not job_id_set:
      raise RuntimeError("Unexpected")

  def __init__(self, j1):
    self.in_sstid_pathid = {}
    self.in_sst_ids = set()

    for l1 in j1["mutant_sst_compaction_migration"]["in_sst"].split(") ("):
      mo = re.match(r"\(?sst_id=(?P<sst_id>\d+).*path_id=(?P<path_id>\d+).*", l1)
      if mo is None:
        raise RuntimeError("Unexpected: [%s]" % l1)
      sst_id = int(mo.group("sst_id"))
      path_id = int(mo.group("path_id"))
      #Cons.P("%d %d" % (sst_id, path_id))
      self.in_sstid_pathid[sst_id] = path_id
      self.in_sst_ids.add(sst_id)
    if len(self.in_sst_ids) == 0:
      raise RuntimeError("Unexpected")
    elif len(self.in_sst_ids) == 1:
      self.migr_type = "SM"
    else:
      self.migr_type = "CM"
    self.in_sstid_str = " ".join(str(i) for i in sorted(self.in_sst_ids))
    #Cons.P(self.in_sstid_pathid)
    #Cons.P(self.in_sst_ids)
    #Cons.P(self.in_sstid_str)

    self.out_path_id = int(j1["mutant_sst_compaction_migration"]["out_sst_path_id"])

    # temp_triggered_single_sst_compaction is not accurate for some reason.
    #     There are temp_triggered_single_sst_compaction=0 and single SSTable compactions.
    #     There are temp_triggered_single_sst_compaction=1 and multiple SSTable compactions.
    #   Ignore it for now. Must be because there has been changed between the flag was set and when a compaction is made.
    # Use the number of SSTables to determine if it's a pure migration or a compaction-migration
    #   The classification may not be 100% accurate, it should be more than 95% accurate since the trivial moves without Mutant were super rare.

    # Constructed later
    self.job_id = None

    # {Output SSTable ID: migration direction}
    #   Migration direction: (S)to slow, (F)to fast, (-)no change
    #   We assign assign these proportional to the number of hot and cold InSsts
    #   The number of output SSTables is not always the same as the number of input SSTables because of duplicated keys.
    self.out_sstid_migrdir = {}

  def __repr__(self):
    return " ".join("%s=%s" % item for item in sorted(vars(self).items()))

  def Included(self, sst_ids):
    for s in self.in_sst_ids:
      if s not in sst_ids:
        return False
    return True

  @staticmethod
  def Get(job_id):
    return CompInfo.jobid_compinfo[job_id]

  def AddOutSstId(self, out_sst_id):
    # We don't know the migration direction at this point
    self.out_sstid_migrdir[out_sst_id] = None

  @staticmethod
  def CalcMigrDirections():
    for k, ci in CompInfo.jobid_compinfo.iteritems():
      ci._CalcMigrDirections()

  def _CalcMigrDirections(self):
    #Cons.P(self.in_sstid_pathid)
    #Cons.P(self.out_path_id)
    #Cons.P(self.out_sstid_migrdir)

    # In storage 0 and 1: fast and slow
    total_in_sst_size = [0, 0]
    for sst_id in self.in_sstid_pathid:
      hc = HowCreated.Get(sst_id)
      total_in_sst_size[hc.PathId()] += hc.Size()
    in_sst0_size_ratio = float(total_in_sst_size[0]) / sum(total_in_sst_size)

    l = len(self.out_sstid_migrdir)
    i = 0
    for sst_id, migrdir in sorted(self.out_sstid_migrdir.iteritems()):
      i += 1
      # in_path_id: what would have been the in_path_id based on the input SSTables' info
      if (i / l) <= in_sst0_size_ratio:
        in_path_id = 0
      else:
        in_path_id = 1
      if in_path_id == self.out_path_id:
        self.out_sstid_migrdir[sst_id] = "N"
      else:
        if self.out_path_id == 0:
          self.out_sstid_migrdir[sst_id] = "F"
        else:
          self.out_sstid_migrdir[sst_id] = "S"
    #Cons.P(self)

  @staticmethod
  def MigrType(job_id, out_sst_id):
    ci = CompInfo.jobid_compinfo[job_id]
    return (ci.migr_type, ci.out_sstid_migrdir[out_sst_id])


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
