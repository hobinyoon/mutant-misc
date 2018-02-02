import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

# How an SSTable was created
class HowCreated:
  sstid_howcreated = {}

  @staticmethod
  def Init():
    HowCreated.sstid_howcreated = {}

  @staticmethod
  def Add(sst_id, j1):
    hc = HowCreated(j1)
    HowCreated.sstid_howcreated[sst_id] = hc
    return hc

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
    self.out_sst_created_from_temp_triggered_single_sst_migration = None

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
