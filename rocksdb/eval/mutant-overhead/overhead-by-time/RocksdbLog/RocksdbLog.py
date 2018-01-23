import errno
import os
import pprint
import re
import sys
import sqlite3

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
from SstEvents import SstEvents
from HowCreated import HowCreated
from CompInfo import CompInfo

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
  fn_rdb_compmigr = _GetFnRocksdbNumCompMigrHisto(fn_metrics_by_time_0, fn_metrics_by_time_1)
  return (fn_metrics_by_time_0, fn_metrics_by_time_1, fn_rdb_compmigr)


def _GetFnRocksdbNumCompMigrHisto(fn0, fn1):
  # Build an index of db_type, hour, how_created, job_id, and number of sstables.

  fn_db = "%s/sst-creation-info.db" % Conf.GetOutDir()
  try:
    os.remove(fn_db)
  except OSError as e:
    if e.errno != errno.ENOENT:
      raise e

  table_schema = """ CREATE TABLE IF NOT EXISTS sst_creation_info (
                      fn text NOT NULL
                      , db_type text NOT NULL
                      , hour integer NOT NULL
                      , sst_id integer NOT NULL
                      , job_id integer NOT NULL
                      , creation_reason text NOT NULL
                      , temp_triggered_single_sst_migr BOOLEAN
                      , migr_dirc text NOT NULL
                    ); """
  conn = sqlite3.connect(fn_db)
  if conn is None:
    raise RuntimeError("Error! cannot create the database connection.")
  cur = conn.cursor()
  cur.execute(table_schema)

  q = """INSERT INTO sst_creation_info (fn, db_type, hour, sst_id, job_id, creation_reason, temp_triggered_single_sst_migr, migr_dirc)
           VALUES (?,?,?,?,?,?,?,?)"""

  for db_type in ["RocksDB", "Mutant"]:
    fn = fn0 if db_type == "RocksDB" else fn1
    with open(fn) as fo:
      for line in fo:
        if line.startswith("#"):
          continue
        line = line.strip()
        t = re.split(r" +", line)
        hour = int(t[1].split(":")[0])

        sst_id = t[6]
        # Ignore when end sst_id is -, which means an sstable was deleted.
        if sst_id == "-":
          continue
        sst_id = int(sst_id)

        job_id = int(t[7])

        # Creation reason: R, F, C, -
        cr = t[8]
        temp_triggered_single_sst_migr = (t[9] == "T")
        migr_dirc = t[10]

        cur.execute(q, (fn, db_type, hour, sst_id, job_id, cr, temp_triggered_single_sst_migr, migr_dirc))
  conn.commit()
  cur.close()

  # TODO: continue from here!
  # https://docs.python.org/2/library/sqlite3.html#row-objects

  conn.row_factory = sqlite3.Row
  cur = conn.cursor()

  #cur.execute("SELECT db_type, hour, creation_reason, temp_triggered_single_sst_migr, migr_dirc, count(*)" \
  #    " FROM sst_creation_info" \
  #    " GROUP BY db_type, hour, creation_reason, temp_triggered_single_sst_migr, migr_dirc")
  #rows = cur.fetchall()
  #for r in rows:
  #  Cons.P(r)

  for db_type in ["RocksDB", "Mutant"]:
    fn = fn0 if db_type == "RocksDB" else fn1
    Cons.P("# %s" % db_type)
    Cons.P("#   fn=%s" % fn)

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE db_type='%s'" % db_type)
    r = cur.fetchone()
    Cons.P("#   num_jobs=%d" % r["cnt"])

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE db_type='%s' and creation_reason='R'" % db_type)
    Cons.P("#   num_jobs_recovery=%d" % cur.fetchone()["cnt"])

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE db_type='%s' and creation_reason='F'" % db_type)
    Cons.P("#   num_jobs_flush=%d" % cur.fetchone()["cnt"])

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE db_type='%s' and creation_reason='C'" % db_type)
    num_comp_jobs_all = cur.fetchone()["cnt"]
    Cons.P("#   num_jobs_comp_all=%d" % num_comp_jobs_all)

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info" \
        " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0"
        % db_type)
    num_jobs_comp_level_triggered = cur.fetchone()["cnt"]
    Cons.P("#   num_jobs_comp_level_triggered=%d" % num_jobs_comp_level_triggered)

    cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
        " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0"
        % db_type)
    num_outssts_comp_level_triggered = cur.fetchone()["cnt"]
    Cons.P("#     num_outssts_comp_level_triggered=%d" % num_outssts_comp_level_triggered)
    Cons.P("#     num_outssts_comp_level_triggered_per_job=%f" % (float(num_outssts_comp_level_triggered) / num_jobs_comp_level_triggered))

    # TODO: figure this out
    #Cons.P("#     num_outssts_comp_level_triggered_compaction_migration=%d" % )

    cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info" \
        " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
        % db_type)
    Cons.P("#   num_jobs_comp_temp_triggered_migr=%d" % cur.fetchone()["cnt"])

    # With a temperature-triggered single-sstable migration, there is always a single input sstable, but there can be multiple output sstables.
    #   Interesting.
    #   All of those happened with a 256MB L0 SSTable in the fast storage becoming cold and being migrated to the slow storage,
    #     making 4 64MB L0 SSTables in the slow storage.
    #   I don't think there is any harm there. It's just the output file is splitted into 4 small ones.
    #   Count each of them as a single migration.
    #
    #cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
    #    " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
    #    % db_type)
    #Cons.P("#     num_outssts_comp_temp_triggered_migr=%d" % cur.fetchone()["cnt"])
    #
    #cur.execute("SELECT job_id, count(distinct(sst_id)) as num_sst_ids FROM sst_creation_info" \
    #    " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1" \
    #    " GROUP BY job_id ORDER BY job_id"
    #    % db_type)
    #for r in cur.fetchall():
    #  if 1 < r["num_sst_ids"]:
    #    Cons.P("#       job_id=%d num_sst_ids=%d" % (r["job_id"], r["num_sst_ids"]))


  sys.exit(0)


    # Check the number of output sstables
#    histo_num_out_sstables = {}
#    for job_id, sst_id_set in fn_jobid_sstidset[fn].iteritems():
#      if len(sst_id_set) not in histo_num_out_sstables:
#        histo_num_out_sstables[len(sst_id_set)] = 1
#      else:
#        histo_num_out_sstables[len(sst_id_set)] += 1
  Cons.P("#   num_out_ssts_per_comp_histo=%s" % histo_num_out_sstables)

  Cons.P("#")
  Cons.P("# r_: RocksDB, m_:Mutant")
  Cons.P("# R: recovery, F: flush, C: compaction. Number of SSTables created by the events")

  Cons.P("# migrs: number of temperature-triggered single-sstable migrations")
  Cons.P("# ossts: output sstables")
  Cons.P("#")

  #fmt = "%1d" \
  #    " %4d %4d %4d %4d %5.2f %4d %4d" \
  #    " %8d %4d %4d %5.2f %4d %4d"
  #Cons.P(Util.BuildHeader(fmt,
  #  "hour" \
  #  " r_Rs" \
  #  " r_Fs" \
  #  " r_RCs" \
  #  " r_ossts_comps" \
  #  " r_ossts_per_comps" \
  #  " r_ossts_comp_migrs" \
  #  " r_ossts_single_migrs" \
  #  \
  #  " m_ossts_flushes" \
  #  " m_rcomps" \
  #  " m_ossts_comps" \
  #  " m_ossts_per_comps" \
  #  " m_ossts_comp_migrs" \
  #  " m_ossts_single_migrs" \
  #  ))

  fmt = "%1d" \
      " %3d %3d %3d"
  Cons.P(Util.BuildHeader(fmt,
    "hour" \
    " r_Rs r_Fs r_Cs" \
    ))

  # Hard coded for now
  max_hour = 10

  for h in range(max_hour):
    # Mutant. Number of compactions not counting migrations.
    m_comps = len(fn_h_jobid_sstidset[fn1][h]) - (fn_h_cr_cnt[fn1][h]["SM"] if "SM" in fn_h_cr_cnt[fn1][h] else 0)

    #  '/home/hobin/work/mutant/misc/rocksdb/eval/mutant-overhead/overhead-by-time/.output/rocksdb-by-time-180119-230659.615': {
    # 0: {creation_reason=R migr_dirc=- temp_triggered_single_sst_migr=-: 1,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 107,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 67,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=T: 3,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 73,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 12,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=-: 11},
    # 1: {creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 209,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=-: 22,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 150,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 146,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 29},
    # 2: {creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 148,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 227,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=-: 4,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 122,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 24},
    # 3: {creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 281,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 255,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 44,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 143,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=-: 3},
    # 4: {creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 177,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 95,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 9,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 182,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 31,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=-: 1},
    # 5: {creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 118,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 197,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 58,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 31},
    # 6: {creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 171,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 225,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 216,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 26},
    # 7: {creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 252,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 193,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 244,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 33},
    # 8: {creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 29,
    #     creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 298,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 8,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 234,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 273},
    # 9: {creation_reason=C migr_dirc=S temp_triggered_single_sst_migr=T: 65,
    #     creation_reason=F migr_dirc=- temp_triggered_single_sst_migr=-: 3,
    #     creation_reason=C migr_dirc=N temp_triggered_single_sst_migr=-: 144,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=-: 17,
    #     creation_reason=C migr_dirc=F temp_triggered_single_sst_migr=T: 39}}}

    Cons.P(fmt % (
        h
        , _GetOr0(fn_h_cr_cnt[fn0][h], CreationReason("R"))
        , _GetOr0(fn_h_cr_cnt[fn0][h], CreationReason("F"))
        , _GetOr0(fn_h_cr_cnt[fn0][h], CreationReason("C"))

        #, len(fn_h_jobid_sstidset[fn0][h])
        #, fn_h_cr_cnt[fn0][h]["C"]
        #, (float(fn_h_cr_cnt[fn0][h]["C"]) / len(fn_h_jobid_sstidset[fn0][h]))
        #, (fn_h_comptype[fn0][h]["CM"] if "CM" in fn_h_comptype[fn0][h] else 0)
        #, (fn_h_comptype[fn0][h]["SM"] if "SM" in fn_h_comptype[fn0][h] else 0)

        #, fn_h_cr_cnt[fn1][h]["F"]
        #, m_comps
        #, fn_h_cr_cnt[fn1][h]["C"]
        #, (float(fn_h_cr_cnt[fn1][h]["C"]) / len(fn_h_jobid_sstidset[fn1][h]))
        #, (fn_h_comptype[fn1][h]["CM"] if "CM" in fn_h_comptype[fn1][h] else 0)
        #, (fn_h_comptype[fn1][h]["SM"] if "SM" in fn_h_comptype[fn1][h] else 0)
        ))

  sys.exit(1)
  fn_out = "%s/rocksdb-sst-creation-cnt-by-reasons-by-time" % Conf.GetOutDir()
  with open(fn_out, "w") as fo:
    fo.write("\n")
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


def _GetOr0(d, k):
  return (d[k] if k in d else 0)


class CreationReason:
  def __init__(self, creation_reason, temp_triggered_single_sst_migr = "-", migr_dirc = "-"):
    # C (pure compaction), MC (migration compaction), M (temperature-triggered single sstable migration)
    self.creation_reason = creation_reason
    self.temp_triggered_single_sst_migr = temp_triggered_single_sst_migr
    # - (no change), S (to slow storage), F (to fast storage)
    self.migr_dirc = migr_dirc

  # Make it hashable by attributes. Needed when you __eq__ is defined
  def __hash__(self):
    return hash(" ".join("%s" % v for k, v in sorted(vars(self).items())))

  def __eq__(self, other):
    s = vars(self)
    o = vars(other)

    for k, v in s.iteritems():
      if v != o[k]:
        return False
    return True

  # Not sure how you can order print dict in a sorted order with pformat(). Tried this, but didn't work.
  #def __lt__(self, other):
  #  s = vars(self)
  #  o = vars(other)

  #  for k, v in sorted(s.iteritems()):
  #    if v >= o[k]:
  #      return False
  #  return True
  
  def __repr__(self):
    return " ".join("%s=%s" % item for item in sorted(vars(self).items()))


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
