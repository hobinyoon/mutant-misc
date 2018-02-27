from contextlib import contextmanager
from multiprocessing import Pool

import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
from SstEvents import SstEvents
from SstInfo import SstInfo
from CompInfo import CompInfo

import StgCost


@contextmanager
def terminating(thing):
  try:
    yield thing
  finally:
    thing.terminate()


def GetFnTimeVsMetrics(fn_ycsb):
  mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb)
  dn_log = mo.group("dn_log")
  job_id = mo.group("job_id")
  exp_dt = mo.group("exp_dt")
  #Cons.P(dn_log)
  #Cons.P(job_id)
  #Cons.P(exp_dt)
  dn_log_job = "%s/%s" % (dn_log, job_id)
  lr = RocksdbLogReader(dn_log_job, exp_dt)
  return (lr.FnMetricByTime(), lr.GetTargetCostChanges())


class RocksdbLogReader:
  def __init__(self, dn_log_job, exp_dt):
    self.fn_out = "%s/rocksdb-by-time-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.sst_events = SstEvents(self, exp_dt)
    self.sst_info = SstInfo()
    self.comp_info = CompInfo(self)
    self.stg_cost = StgCost.StgCost(exp_dt)

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

          # Storage pricing. Fast and slow.
          #   We parse the 2 storage configuration for now.
          #   You don't need this for the baseline, unmodified DB, since the unit cost is always the same.
          # 2018/01/23-22:53:48.875126 7f3300cd8700   stg_cost_list: 0.528000 0.045000
          elif "   stg_cost_list: " in line:
            self.stg_cost.SetStgPricing(line)

          # 2018/01/23-22:53:48.875128 7f3300cd8700   stg_cost_slo: 0.300000
          elif "   stg_cost_slo: " in line:
            self.stg_cost.SetTargetCost(line)

          # 2018/01/23-22:53:48.875130 7f3300cd8700   stg_cost_slo_epsilon: 0.020000
          elif "   stg_cost_slo_epsilon: " in line:
            self.stg_cost.SetMigrationResistance(line)

          # 2018/02/27-17:27:33.745680 7fcbc1536700 EVENT_LOG_v1 {"time_micros": 1519752453745660, "Set target_cost to ": 0.2}
          elif "Set target_cost to" in line:
            self.stg_cost.SetCostChange(line)

          # 2018/02/27-16:49:17.959334 7ff0ed2b2700 EVENT_LOG_v1 {"time_micros": 1519750157959324, "mutant_sst_opened": {"file_number": 2274, "file_size":
          # 10950641, "path_id": 0, "level": 1}}
          elif "\"mutant_sst_opened\": " in line:
            self.sst_events.Created1(line)

          # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
          # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
          # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
          # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
          elif "\"event\": \"table_file_creation\"" in line:
            self.sst_events.Created2(line)

          # 2018/01/01-05:33:49.183505 7f97d0ff1700 EVENT_LOG_v1 {"time_micros": 1514784829183496, "job": 6, "event": "table_file_deletion", "file_number": 21}
          elif "\"event\": \"table_file_deletion\"" in line:
            self.sst_events.Deleted(line)

          # 2018/01/23-00:13:13.593310 7fa321da9700 EVENT_LOG_v1 {"time_micros": 1516666393593302, "mutant_calc_out_sst_path_id": {"in_sst": "(sst_id=16
          # temp=57.189 level=0 path_id=0 size=258425431 age=30)", "in_sst_temp": "57.188590", "sst_ott": 3176.66, "out_sst_path_id": 1,
          # "temp_triggered_single_sst_compaction": 1}}
          elif "\"mutant_calc_out_sst_path_id\"" in line:
            self.comp_info.SetTempTriggeredSingleSstMigr(line)

          # Figure out how an SSTable is created
          # (a) start building CompInfo
          # 2018/01/05-08:40:21.078219 7fd13ffff700 EVENT_LOG_v1 {"time_micros": 1515141621078214, "mutant_sst_compaction_migration": {"in_sst": "(sst_id=16
          # temp=57.345 level=0 path_id=0 size=258423184 age=30) (sst_id=13 temp=3738.166 level=0 path_id=1 size=118885 age=440)", "out_sst_path_id": 1,
          # "temp_triggered_single_sst_compaction": 1}}
          #
          # Some SSTables are created without this log, meaning not going through _CalcOutputPathId(). Use the other one.
          #elif "mutant_sst_compaction_migration" in line:
          #  if not self.migrate_sstables:
          #    continue
          #  self.comp_info.Add(line)

          # Build CompInfo
          #   We manually parse this just because there are multiple keys with "files_L0" and json would probably not be able to parse it
          #   2018/01/05-08:40:21.078303 7fd13ffff700 EVENT_LOG_v1 {"time_micros": 1515141621078294, "job": 5, "event": "compaction_started", "files_L0": [16,
          #   13], "files_L0": [16, 13], "score": 0, "input_data_size": 517084138}
          elif "compaction_started" in line:
            self.comp_info.SetCompStarted(line)

          # (c) Assign out_sst_info to CompInfo using job_id. It is done when parsing table_file_creation above.

      self.comp_info.CalcMigrDirections()
      self.sst_events.Write(self.fn_out)
      self.stg_cost.AddStatToFile(self.fn_out)

  def FnMetricByTime(self):
    return self.fn_out

  def GetTargetCostChanges(self):
    with open(self.fn_out) as fo:
      for line in fo:
        #   cost_changes=[0:00:00 0.400000, 0:15:10.288680 0.200000, 0:30:10.288906 0.300000]
        mo = re.match(r"#   cost_changes=\[(?P<v>(\d|:|\.|,| )+)\]", line)
        if mo:
          rel_time = []
          target_cost = []
          for v in mo.group("v").split(", "):
            v1 = v.split(" ")
            rel_time.append(v1[0])
            target_cost.append(v1[1])
          return (" ".join(rel_time), " ".join(target_cost))


    raise RuntimeError("Unexpected: %s" % self.fn_out)

  def __repr__(self):
    return "<%s>" % " ".join("%s=%s" % item for item in sorted(vars(self).items()))
