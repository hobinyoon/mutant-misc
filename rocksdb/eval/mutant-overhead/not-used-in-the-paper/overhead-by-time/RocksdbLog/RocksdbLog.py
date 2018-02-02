import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
from SstEvents import SstEvents
from HowCreated import HowCreated
from CompInfo import CompInfo
import CompMigrStat

def GenDataFilesForGnuplot():
  dn_base = Conf.GetDir("dn_base")

  # Analyze the number of compactions and migrations with
  #   (a) an unmodified DB as a baseline
  #   and (b) Mutant
  fns_ycsb = []
  log_readers = []
  for db_type in ["unmodified_db", "io_overhead"]:
    fn_ycsb = "%s/%s" % (dn_base, Conf.Get(db_type))
    mo = re.match(r"(?P<dn_log>.+)/(?P<job_id>\d\d\d\d\d\d-\d\d\d\d\d\d)/ycsb/(?P<exp_dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d).+", fn_ycsb)
    dn_log = mo.group("dn_log")
    job_id = mo.group("job_id")
    exp_dt = mo.group("exp_dt")
    #Cons.P(dn_log)
    #Cons.P(job_id)
    #Cons.P(exp_dt)
    dn_log_job = "%s/%s" % (dn_log, job_id)
    log_readers.append(RocksdbLogReader(dn_log_job, exp_dt))

  fn_metrics_by_time_0 = log_readers[0].FnMetricByTime()
  fn_metrics_by_time_1 = log_readers[1].FnMetricByTime()
  fn_rdb_compmigr = CompMigrStat.GetFnStat(fn_metrics_by_time_0, fn_metrics_by_time_1)
  return (fn_metrics_by_time_0, fn_metrics_by_time_1, fn_rdb_compmigr)


class RocksdbLogReader:
  def __init__(self, dn_log_job, exp_dt):
    self.fn_out = "%s/rocksdb-by-time-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    # These classes rely on the global data structures, thus not thread-safe. Fine for now.
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
            HowCreated.migrate_sstables = self.migrate_sstables

          # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
          # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
          # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
          # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
          elif "\"event\": \"table_file_creation\"" in line:
            SstEvents.Created(line)

          # 2018/01/01-05:33:49.183505 7f97d0ff1700 EVENT_LOG_v1 {"time_micros": 1514784829183496, "job": 6, "event": "table_file_deletion", "file_number": 21}
          elif "\"event\": \"table_file_deletion\"" in line:
            SstEvents.Deleted(line)

          # 2018/01/23-00:13:13.593310 7fa321da9700 EVENT_LOG_v1 {"time_micros": 1516666393593302, "mutant_calc_out_sst_path_id": {"in_sst": "(sst_id=16
          # temp=57.189 level=0 path_id=0 size=258425431 age=30)", "in_sst_temp": "57.188590", "sst_ott": 3176.66, "out_sst_path_id": 1,
          # "temp_triggered_single_sst_compaction": 1}}
          elif "\"mutant_calc_out_sst_path_id\"" in line:
            CompInfo.SetTempTriggeredSingleSstMigr(line)

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
          #  CompInfo.Add(line)

          # Build CompInfo
          #   We manually parse this just because there are multiple keys with "files_L0" and json would probably not be able to parse it
          #   2018/01/05-08:40:21.078303 7fd13ffff700 EVENT_LOG_v1 {"time_micros": 1515141621078294, "job": 5, "event": "compaction_started", "files_L0": [16,
          #   13], "files_L0": [16, 13], "score": 0, "input_data_size": 517084138}
          elif "compaction_started" in line:
            CompInfo.SetCompStarted(line)

          # (c) Assign out_sst_info to CompInfo using job_id. It is done when parsing table_file_creation above.

      CompInfo.CalcMigrDirections()
      SstEvents.Write(self.fn_out)

  def FnMetricByTime(self):
    return self.fn_out
