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
import CompMigrStat
import StgCost


@contextmanager
def terminating(thing):
  try:
    yield thing
  finally:
    thing.terminate()


def GetFnCostSloEpsilonVsMetrics():
  fn_out = "%s/cost-slo-epsilon-vs-metrics" % Conf.GetOutDir()
  if os.path.isfile(fn_out):
    return fn_out

  dn_base = Conf.GetDir("dn_base")
  # {cost_slo_epsilon: fn}
  cse_fn ={}
  for cost_slo_epsilon, fn0 in Conf.Get("by_cost_slo_epsilons").iteritems():
    fn = "%s/%s" % (dn_base, fn0)
    cse_fn[cost_slo_epsilon] = fn
  #Cons.P(pprint.pformat(cse_fn))

  params = []
  for cost_slo_epsilon, fn_ycsb_log in sorted(cse_fn.iteritems()):
    params.append(fn_ycsb_log)

  parallel_processing = True
  if parallel_processing:
    with terminating(Pool()) as pool:
      result = pool.map(GetFnTimeVsMetrics, params)
  else:
    result = []
    for p in params:
      result.append(GetFnTimeVsMetrics(p))
  #Cons.P(result)

  cse_outfn = {}
  i = 0
  for cost_slo_epsilon, fn_ycsb_log in sorted(cse_fn.iteritems()):
    cse_outfn[cost_slo_epsilon] = result[i]
    i += 1

  with open(fn_out, "w") as fo:
    fo.write("# CSE: Storge cost SLO epsilon\n")
    fo.write("# JR: jobs_recovery\n")
    fo.write("# JF: jobs_flush\n")
    fo.write("# JC: jobs_compaction\n")
    fo.write("#   JCL: jobs_comp_leveled_organization_triggered\n")
    fo.write("#   SSCL: total_sst_size_comp_level_triggered_in_gb\n")
    fo.write("#   SSCLCM: total_sst_size_comp_level_triggered_comp_migrs_in_gb\n")
    fo.write("#     SSCLCMS: total_sst_size_comp_level_triggered_comp_migrs_to_slow_in_gb\n")
    fo.write("#     SSCLCMF: total_sst_size_comp_level_triggered_comp_migrs_to_fast_in_gb\n")
    fo.write("# JCT: jobs_comp_temp_triggered_migr\n")
    fo.write("#   SSCT: total_sst_size_comp_temp_triggered_migr_in_gb\n")
    fo.write("#     SSCTS: To slow storage\n")
    fo.write("#     SSCTF: To fast storage\n")
    fo.write("\n")

    fmt = "%4.2f %8.6f %8.6f %8.6f %8.6f %1d %2d %4d" \
        " %4d %7.3f %7.3f %7.3f %7.3f" \
        " %4d %7.3f %7.3f %7.3f"
    header = Util.BuildHeader(fmt, "CSE" \
        " stg_unit_cost_$_gb_month" \
        " stg_cost_$" \
        " fast_stg_cost_$" \
        " slow_stg_cost_$" \
        " JR" \
        " JF" \
        " JC" \
          " JCL" \
          " SSCL" \
          " SSCLCM" \
            " SSCLCMS" \
            " SSCLCMF" \
        " JCT" \
          " SSCT" \
            " SSCTS" \
            " SSCTF" \
        )
    fo.write(header + "\n")

    for cost_slo_epsilon, fn1 in sorted(cse_outfn.iteritems()):
      kvs = [
          ["total_stg_unit_cost", None]
          , ["total_stg_cost", None]
          , ["fast_stg_cost", None]
          , ["slow_stg_cost", None]
          , ["num_jobs_recovery", None]
          , ["num_jobs_flush", None]
          , ["num_jobs_comp_all", None]
            , ["num_jobs_comp_level_triggered", None]
            , ["total_sst_size_comp_level_triggered_in_gb", None]
            , ["total_sst_size_comp_level_triggered_comp_migrs_in_gb", None]
              , ["total_sst_size_comp_level_triggered_comp_migrs_to_slow_in_gb", None]
              , ["total_sst_size_comp_level_triggered_comp_migrs_to_fast_in_gb", None]
          , ["num_jobs_comp_temp_triggered_migr", None]
            , ["total_sst_size_comp_temp_triggered_migr", None]
              , ["total_sst_size_comp_temp_triggered_migr_to_slow", None]
              , ["total_sst_size_comp_temp_triggered_migr_to_fast", None]
          ]

      with open(fn1) as fo1:
        for line in fo1:
          if not line.startswith("#"):
            continue

          for kv in kvs:
            k = kv[0]
            mo = re.match(r".+%s=(?P<v>(\d|\.)+)" % k, line)
            if mo:
              kv[1] = float(mo.group("v"))
              continue

      try:
        fo.write((fmt + "\n") % (
          cost_slo_epsilon
          , kvs[0][1]
          , kvs[1][1]
          , kvs[2][1]
          , kvs[3][1]
          , kvs[4][1]
          , kvs[5][1]
          , kvs[6][1]
          , kvs[7][1]
          , kvs[8][1]
          , kvs[9][1]
          , kvs[10][1]
          , kvs[11][1]
          , kvs[12][1]
          , kvs[13][1]
          , kvs[14][1]
          , kvs[15][1]
          ))
      except TypeError as e:
        Cons.P(fn1)
        raise e

  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


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
  return lr.FnMetricByTime()


def GetFnCompareTwo():
  dn_base = Conf.GetDir("dn_base")

  # Analyze the number of compactions and migrations with
  #   (a) an unmodified DB as a baseline
  #   and (b) Mutant
  fn_metrics_by_time = []
  for i in range(2):
    fn_ycsb = "%s/%s" % (dn_base, Conf.Get(i))
    fn_metrics_by_time.append(GetFnTimeVsMetrics(fn_ycsb))

  fn_rdb_compmigr = CompMigrStat.GetFnStat(fn_metrics_by_time[0], fn_metrics_by_time[1])
  return (fn_metrics_by_time, fn_rdb_compmigr)


class RocksdbLogReader:
  def __init__(self, dn_log_job, exp_dt):
    self.fn_out = "%s/rocksdb-by-time-%s" % (Conf.GetOutDir(), exp_dt)
    if os.path.isfile(self.fn_out):
      return

    self.sst_events = SstEvents(self, exp_dt)
    self.sst_info = SstInfo()
    self.comp_info = CompInfo(self)

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

      self.stg_pricing = None
      self.stg_cost_slo = None
      self.stg_cost_slo_epsilon = None

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
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_list: (?P<v0>(\d|\.)+) (?P<v1>(\d|\.)+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)
            self.stg_pricing = [float(mo.group("v0")), float(mo.group("v1"))]

          # 2018/01/23-22:53:48.875128 7f3300cd8700   stg_cost_slo: 0.300000
          elif "   stg_cost_slo: " in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_slo: (?P<v>(\d|\.)+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)
            self.stg_cost_slo = float(mo.group("v"))

          # 2018/01/23-22:53:48.875130 7f3300cd8700   stg_cost_slo_epsilon: 0.020000
          elif "   stg_cost_slo_epsilon: " in line:
            mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_slo_epsilon: (?P<v>(\d|\.)+)", line)
            if mo is None:
              raise RuntimeError("Unexpected: [%s]" % line)
            self.stg_cost_slo_epsilon = float(mo.group("v"))

          # 2017/10/13-20:41:54.872056 7f604a7e4700 EVENT_LOG_v1 {"time_micros": 1507927314871238, "cf_name": "usertable", "job": 3, "event":
          # "table_file_creation", "file_number": 706, "file_size": 258459599, "path_id": 0, "table_properties": {"data_size": 256772973, "index_size": 1685779,
          # "filter_size": 0, "raw_key_size": 6767934, "raw_average_key_size": 30, "raw_value_size": 249858360, "raw_average_value_size": 1140,
          # "num_data_blocks": 54794, "num_entries": 219174, "filter_policy_name": "", "reason": kFlush, "kDeletedKeys": "0", "kMergeOperands": "0"}}
          elif "\"event\": \"table_file_creation\"" in line:
            self.sst_events.Created(line)

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
      CompMigrStat.AddStatToFile(self.fn_out)
      self.stg_cost = StgCost.StgCost(self)
      self.stg_cost.AddStatToFile(self.fn_out)

  def FnMetricByTime(self):
    return self.fn_out

  def __repr__(self):
    return "<%s>" % " ".join("%s=%s" % item for item in sorted(vars(self).items()))
