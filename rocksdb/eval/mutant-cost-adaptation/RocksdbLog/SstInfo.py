import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class SstInfo:
  def __init__(self):
    self.sstid_info = {}

  def Add(self, sst_id, j1):
    e = SiEntry(j1)
    self.sstid_info[sst_id] = e

  def Update(self, sst_id, j1):
    e = self.sstid_info[sst_id]
    e.Update(j1)
    return e

  def Get(self, sst_id):
    return self.sstid_info[sst_id] if sst_id in self.sstid_info else None

  def __repr__(self):
    s = []
    for k, v in sorted(vars(self).items()):
      if k == "sstid_info":
        s.append("len(%s)=%d" % (k, len(v)))
      else:
        s.append("%s=%s" % (k, v))
    return "<%s>" % " ".join(s)


class SiEntry:
  def __init__(self, j1):
    j2 = j1["mutant_sst_opened"]
    self.sst_id = int(j2["file_number"])
    self.path_id = int(j2["path_id"])
    self.sst_size = int(j2["file_size"])
    self.level = int(j2["level"])
    if self.level < 0:
      Cons.P("Interesting: sst_id=%d level=%d" % (self.sst_id, self.level))
      self.level = 0

    self.reason = None
    self.job_id = None

  def Update(self, j1):
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

  def __repr__(self):
    return "<%s>" % " ".join("%s=%s" % item for item in sorted(vars(self).items()))

  def Size(self):
    return self.sst_size

  def PathId(self):
    return self.path_id

  def Reason(self):
    return self.reason

  def JobId(self):
    return self.job_id

  def Level(self):
    return self.level
