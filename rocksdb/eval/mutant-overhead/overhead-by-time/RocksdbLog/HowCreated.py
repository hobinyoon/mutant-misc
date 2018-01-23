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



# TODO
#    self.in_sstid_pathid = {}
#    self.in_sst_ids = set()
#
#    for l1 in j1["mutant_sst_compaction_migration"]["in_sst"].split(") ("):
#      mo = re.match(r"\(?sst_id=(?P<sst_id>\d+).*path_id=(?P<path_id>\d+).*", l1)
#      if mo is None:
#        raise RuntimeError("Unexpected: [%s]" % l1)
#      sst_id = int(mo.group("sst_id"))
#      path_id = int(mo.group("path_id"))
#      #Cons.P("%d %d" % (sst_id, path_id))
#      self.in_sstid_pathid[sst_id] = path_id
#      self.in_sst_ids.add(sst_id)
#    if len(self.in_sst_ids) == 0:
#      raise RuntimeError("Unexpected")
#    # TODO: fix this one. You can rely on temp_triggered_single_sst_compaction now
#    elif len(self.in_sst_ids) == 1:
#      self.migr_type = "SM"
#    else:
#      self.migr_type = "CM"
#    self.in_sstid_str = " ".join(str(i) for i in sorted(self.in_sst_ids))
#    #Cons.P(self.in_sstid_pathid)
#    #Cons.P(self.in_sst_ids)
#    #Cons.P(self.in_sstid_str)
#
#    self.out_path_id = int(j1["mutant_sst_compaction_migration"]["out_sst_path_id"])
#
#    # temp_triggered_single_sst_compaction is not accurate for some reason.
#    #     There are temp_triggered_single_sst_compaction=0 and single SSTable compactions.
#    #     There are temp_triggered_single_sst_compaction=1 and multiple SSTable compactions.
#    #   Ignore it for now. Must be because there has been changed between the flag was set and when a compaction is made.
#    # Use the number of SSTables to determine if it's a pure migration or a compaction-migration
#    #   The classification may not be 100% accurate, it should be more than 95% accurate since the trivial moves without Mutant were super rare.
#
#    # A job_id will be assigned later
#    self.job_id = None
#
#    # {Output SSTable ID: migration direction}
#    #   Migration direction: (S)to slow, (F)to fast, (-)no change
#    #   We assign assign these proportional to the number of hot and cold InSsts
#    #   The number of output SSTables is not always the same as the number of input SSTables because of duplicated keys.
#    self.out_sstid_migrdir = {}


    # TODO
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
