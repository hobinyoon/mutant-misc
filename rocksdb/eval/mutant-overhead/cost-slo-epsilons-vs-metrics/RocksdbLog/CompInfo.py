import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

from HowCreated import HowCreated

class CompInfo:
  def __init__(self):
    # {job_id: CiEntry()}
    self.jobid_cientry = {}
    # Input SSTable IDs that caused temperature-triggered single-sstable migration
    #   The set contains sst ids from multiple jobs
    self.ttssm_in_sst_ids = set()

  def AddOutSstInfo(self, j1):
    job_id = int(j1["job"])
    if job_id not in self.jobid_cientry:
      raise RuntimeError("Unexpected")
    e = self.jobid_cientry[job_id]
    e.AddOutSstInfo(j1)

  def SetCompStarted(self, line):
    e = CiEntry(line)
    if e.job_id in self.jobid_cientry:
      raise RuntimeError("Unexpected")
    self.jobid_cientry[e.job_id] = e

  def Get(self, job_id):
    return self.jobid_cientry[job_id]

  def TempTriggeredSingleSstMigr(self, job_id):
    if job_id not in self.jobid_cientry:
      return False

    e = self.jobid_cientry[job_id]
    ttssm = None
    # Make sure all input sstables lead to the same value, whether the compaction was triggered by a temperature change.
    for in_sst_id in e.in_sst_ids:
      ttssm1 = (in_sst_id in self.ttssm_in_sst_ids)

      if ttssm is None:
        ttssm = ttssm1
      else:
        if ttssm != ttssm1:
          raise RuntimeError("Unexpected")

    if ttssm is None:
      raise RuntimeError("Unexpected")
    return ttssm

  def CalcMigrDirections(self):
    for k, e in self.jobid_cientry.iteritems():
      e.CalcMigrDirections()

  def MigrDirc(self, job_id, out_sst_id):
    e = self.jobid_cientry[job_id]
    osi = e.out_ssts[out_sst_id]
    return osi.migr_dirc

  # Set whether a compaction is a temperature-triggered single-sstable migration or not.
  #   This is correct 99.9% of the times, but sometimes the migration can be cancelled if the input and output path_ids are the same.
  #     We'll see how the case can be corrected.
  #
  # 2018/01/23-00:13:13.593310 7fa321da9700 EVENT_LOG_v1 {"time_micros": 1516666393593302, "mutant_calc_out_sst_path_id": {"in_sst": "(sst_id=16
  # temp=57.189 level=0 path_id=0 size=258425431 age=30)", "in_sst_temp": "57.188590", "sst_ott": 3176.66, "out_sst_path_id": 1,
  # "temp_triggered_single_sst_compaction": 1}}
  def SetTempTriggeredSingleSstMigr(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    j = mo.group("json")
    try:
      j1 = json.loads(j)
    except ValueError as e:
      Cons.P("%s [%s]" % (e, line))
      sys.exit(1)

    if j1["mutant_calc_out_sst_path_id"]["temp_triggered_single_sst_compaction"] == 0:
      return

    out_path_id = int(j1["mutant_calc_out_sst_path_id"]["out_sst_path_id"])

    tokens = j1["mutant_calc_out_sst_path_id"]["in_sst"].split(") (")
    # This is not supposed to happen
    if len(tokens) != 1:
      raise RuntimeError("Unexpected. %d SSTables in a temperature-triggered migration. [%s]" % (len(tokens), line))
    t = tokens[0]
    # (sst_id=16 temp=57.189 level=0 path_id=0 size=258425431 age=30)
    mo = re.match(r"\(?sst_id=(?P<sst_id>\d+).*path_id=(?P<path_id>\d+).*", t)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    in_sst_id = int(mo.group("sst_id"))
    in_path_id = int(mo.group("path_id"))
    if in_path_id == out_path_id:
      return
    self.ttssm_in_sst_ids.add(in_sst_id)


class CiEntry:
  # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
  # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
  # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
  # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
  def __init__(self, line):
    # {out_sst_id: OutSstInfo()}
    self.out_ssts = {}

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

    # Exact match is supposed to be done here. Was going to used the merged sstable ID string.
    #   But some grandparent SSTables were missing.
    #     While fixing the error, work with the old ones by doing an inclusion test instead.
    self.in_sst_ids = set()
    for i in range(10):
      k = "files_L%d" % i
      if k not in j1:
        continue
      #Cons.P(j1[k])
      for sst_id in j1[k]:
        self.in_sst_ids.add(sst_id)

    self.job_id = int(j1["job"])

  def __repr__(self):
    return " ".join("%s=%s" % item for item in sorted(vars(self).items()))

  def AddOutSstInfo(self, j1):
    osi = OutSstInfo(j1)
    self.out_ssts[osi.sst_id] = osi
    #Cons.P(j1)
    #Cons.P(self)

  def CalcMigrDirections(self):
    #Cons.P(self)

    # In storage 0 and 1: fast and slow
    total_in_sst_sizes = [0, 0]
    for in_sst_id in self.in_sst_ids:
      hc = HowCreated.Get(in_sst_id)
      total_in_sst_sizes[hc.PathId()] += hc.Size()
    in_sst0_size_ratio = float(total_in_sst_sizes[0]) / sum(total_in_sst_sizes)
    #Cons.P("total_in_sst_sizes=%s in_sst0_size_ratio=%d" % (total_in_sst_sizes, in_sst0_size_ratio))

    # self.out_ssts={13: how_created=None migr_dirc=None path_id=1 sst_id=13}
    l = len(self.out_ssts)
    i = 0
    for out_sst_id, v in sorted(self.out_ssts.iteritems()):
      i += 1
      # path_id_before: what the output SSTable's path_id would have been. It is for assigning the migration direction.
      #   It is calculated based on the input SSTables' path_ids.
      if (i / l) <= in_sst0_size_ratio:
        path_id_before = 0
      else:
        path_id_before = 1
      v.SetMigrDirc(path_id_before)


class OutSstInfo:
  def __init__(self, j1):
    self.sst_id = j1["file_number"]
    self.path_id = j1["path_id"]

    # Created from a pure compaction, compaction-migration, or migration.
    self.how_created = None

    # Migration direction
    self.migr_dirc = None

  def SetMigrDirc(self, path_id_before):
    if path_id_before == self.path_id:
      self.migr_dirc = "N"
    else:
      if self.path_id == 0:
        self.migr_dirc = "F"
      else:
        self.migr_dirc = "S"

  def __repr__(self):
    return " ".join("%s=%s" % item for item in sorted(vars(self).items()))
