import errno
import os
import re
import sqlite3
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf

def GetFnStat(fn0, fn1):
  conn = _GenDB(fn0, fn1)

  # https://docs.python.org/2/library/sqlite3.html#row-objects
  conn.row_factory = sqlite3.Row
  cur = conn.cursor()

  _OverallStat(cur, fn0, fn1)
  _HourlyStat(cur)


def _GenDB(fn0, fn1):
  with Cons.MT("Building a stat DB ..."):
    # Put the SSTable creation info in a DB and generate statistics
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
                        , sst_size integer NOT NULL
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

    q = """INSERT INTO sst_creation_info (fn, db_type, hour, sst_id, sst_size, job_id, creation_reason, temp_triggered_single_sst_migr, migr_dirc)
             VALUES (?,?,?,?,?,?,?,?,?)"""

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

          sst_size = int(t[5])

          job_id = int(t[7])

          # Creation reason: R, F, C, -
          cr = t[8]
          temp_triggered_single_sst_migr = (t[9] == "T")
          migr_dirc = t[10]

          cur.execute(q, (fn, db_type, hour, sst_id, sst_size, job_id, cr, temp_triggered_single_sst_migr, migr_dirc))
    conn.commit()
    cur.close()
    return conn


def _OverallStat(cur, fn0, fn1):
  with Cons.MT("Overall stat ..."):
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

      # Distribution of the number of output SSTables per job
      cur.execute("SELECT job_id, count(distinct(sst_id)) as num_ssts FROM sst_creation_info" \
          " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0" \
          " GROUP BY job_id ORDER BY job_id"
          % db_type)
      numssts_cnt = {}
      for r in cur.fetchall():
        c = r["num_ssts"]
        if c not in numssts_cnt:
          numssts_cnt[c] = 1
        else:
          numssts_cnt[c] += 1
      Cons.P("#       %s" % numssts_cnt)

      cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
          " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('-', 'N')"
          % db_type)
      Cons.P("#     num_outssts_comp_level_triggered_regular_compaction=%d" % cur.fetchone()["cnt"])

      cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
          " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('S', 'F')"
          % db_type)
      Cons.P("#     num_outssts_comp_level_triggered_compaction_migration=%d" % cur.fetchone()["cnt"])

      if True:
        # From the SSTables created from compaction-migrations
        #   There are more SSTables that get migrated to the slow storage than to the fast storage. Makes sense, since they get old in general.
        cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
            " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('S')"
            % db_type)
        Cons.P("#     num_outssts_comp_level_triggered_compaction_migration_to_slow_storage=%d" % cur.fetchone()["cnt"])

        if False:
          cur.execute("SELECT job_id, count(distinct(sst_id)) as num_ssts FROM sst_creation_info" \
              " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('S')" \
              " GROUP BY job_id ORDER BY job_id"
              % db_type)
          for r in cur.fetchall():
            Cons.P("#       job_id=%d num_ssts=%d" % (r["job_id"], r["num_ssts"]))

        cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
            " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('F')"
            % db_type)
        Cons.P("#     num_outssts_comp_level_triggered_compaction_migration_to_fast_storage=%d" % cur.fetchone()["cnt"])

        if False:
          cur.execute("SELECT job_id, count(distinct(sst_id)) as num_ssts FROM sst_creation_info" \
              " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('F')" \
              " GROUP BY job_id ORDER BY job_id"
              % db_type)
          for r in cur.fetchall():
            Cons.P("#       job_id=%d num_ssts=%d" % (r["job_id"], r["num_ssts"]))

      cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info" \
          " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
          % db_type)
      Cons.P("#   num_jobs_comp_temp_triggered_migr=%d" % cur.fetchone()["cnt"])

      if False:
        # With a temperature-triggered single-sstable migration, there is always a single input sstable, but there can be multiple output sstables.
        #   Interesting.
        #   All of those happened with a 256MB L0 SSTable in the fast storage becoming cold and being migrated to the slow storage,
        #     making 4 64MB L0 SSTables in the slow storage.
        #   I don't think there is any harm there. It's just the output file is splitted into 4 small ones.
        #   Count each of them as a single migration.
        cur.execute("SELECT count(distinct(sst_id)) as cnt FROM sst_creation_info" \
            " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
            % db_type)
        Cons.P("#     num_outssts_comp_temp_triggered_migr=%d" % cur.fetchone()["cnt"])

        cur.execute("SELECT job_id, count(distinct(sst_id)) as num_ssts FROM sst_creation_info" \
            " WHERE db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1" \
            " GROUP BY job_id ORDER BY job_id"
            % db_type)
        for r in cur.fetchall():
          if 1 < r["num_ssts"]:
            Cons.P("#       job_id=%d num_ssts=%d" % (r["job_id"], r["num_ssts"]))


def _HourlyStat(cur):
  with Cons.MT("Hourly stat ..."):
    Cons.P("# Left set of columns are for RocksDB, right one is for Mutant")
    Cons.P("# J: all jobs")
    Cons.P("# JR: recovery jobs")
    Cons.P("# JF: flush jobs")
    Cons.P("# JC: compaction jobs")
    Cons.P("#   JCL: compaction jobs. leveled organization triggered")
    Cons.P("#     SCL: sstables created. leveled organization triggered")
    Cons.P("#       SPJCL: sstables created / job. leveled organization triggered")
    Cons.P("#     SSCL: sum of the sstable sizes created. leveled organization triggered. In GB.")
    Cons.P("#     SCLR: sstables created. leveled organization triggered. regular compactions")
    Cons.P("#     SCLCM: sstables created. leveled organization triggered. compaction-migrations")
    Cons.P("#   JCT: compaction jobs. temperature-triggered single-sstable migration")
    Cons.P("#     SSCT: sum of the sstable sizes created. temperature-triggered single-sstable migration. In GB.")
    Cons.P("#")

    fmt = "%1d" \
        " %2d %1d %1d %2d %2d" \
          " %3d %5.3f %4.0f %3d %3d %2d %4.0f" \
        " %6d %1d %1d %3d %3d" \
          " %3d %5.3f %4.0f %3d %3d %3d %4.0f"
    Cons.P(Util.BuildHeader(fmt, "hour" \
        " J JR JF JC JCL" \
          " SCL SPJCL SSCL SCLR SCLCM JCT SSCT" \
        " J JR JF JC JCL" \
          " SCL SPJCL SSCL SCLR SCLCM JCT SSCT"
        ))

    for hour in range(10):
      j = {}
      j_r = {}
      j_f = {}
      j_c = {}
      j_c_l = {}
      s_c_l = {}
      spj_c_l = {}
      ss_c_l = {}
      s_c_l_r = {}
      s_c_l_cm = {}
      j_c_t = {}
      ss_c_t = {}
      for db_type in ["R", "M"]:
        db_type_str = "RocksDB" if db_type == "R" else "Mutant"
        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE hour=%d and db_type='%s'" % (hour, db_type_str))
        j[db_type] = cur.fetchone()["cnt"]
        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE hour=%d and db_type='%s' and creation_reason='R'" % (hour, db_type_str))
        j_r[db_type] = cur.fetchone()["cnt"]
        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE hour=%d and db_type='%s' and creation_reason='F'" % (hour, db_type_str))
        j_f[db_type] = cur.fetchone()["cnt"]
        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info WHERE hour=%d and db_type='%s' and creation_reason='C'" % (hour, db_type_str))
        j_c[db_type] = cur.fetchone()["cnt"]

        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0"
            % (hour, db_type_str))
        j_c_l[db_type] = cur.fetchone()["cnt"]

        cur.execute("SELECT count(sst_id) as cnt FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0"
            % (hour, db_type_str))
        s_c_l[db_type] = cur.fetchone()["cnt"]
        spj_c_l[db_type] = 0 if j_c_l[db_type] == 0 else (float(s_c_l[db_type]) / j_c_l[db_type])

        cur.execute("SELECT sum(sst_size) as v FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0"
            % (hour, db_type_str))
        ss_c_l[db_type] = cur.fetchone()["v"]
        if ss_c_l[db_type] is None:
          ss_c_l[db_type] = 0
        ss_c_l[db_type] = float(ss_c_l[db_type]) / 1024 / 1024 / 1024

        cur.execute("SELECT count(sst_id) as cnt FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('-', 'N')"
            % (hour, db_type_str))
        s_c_l_r[db_type] = cur.fetchone()["cnt"]

        cur.execute("SELECT count(sst_id) as cnt FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=0 and migr_dirc IN ('S', 'F')"
            % (hour, db_type_str))
        s_c_l_cm[db_type] = cur.fetchone()["cnt"]

        cur.execute("SELECT count(distinct(job_id)) as cnt FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
            % (hour, db_type_str))
        j_c_t[db_type] = cur.fetchone()["cnt"]

        cur.execute("SELECT sum(sst_size) as v FROM sst_creation_info" \
            " WHERE hour=%d and db_type='%s' and creation_reason='C' and temp_triggered_single_sst_migr=1"
            % (hour, db_type_str))
        ss_c_t[db_type] = cur.fetchone()["v"]
        if ss_c_t[db_type] is None:
          ss_c_t[db_type] = 0
        ss_c_t[db_type] = float(ss_c_t[db_type]) / 1024 / 1024 / 1024

      Cons.P(fmt % (hour
        , j["R"], j_r["R"], j_f["R"], j_c["R"], j_c_l["R"]
          , s_c_l["R"], spj_c_l["R"], ss_c_l["R"], s_c_l_r["R"], s_c_l_cm["R"], j_c_t["R"], ss_c_t["R"]
        , j["M"], j_r["M"], j_f["M"], j_c["M"], j_c_l["M"]
          , s_c_l["M"], spj_c_l["M"], ss_c_l["M"], s_c_l_r["M"], s_c_l_cm["M"], j_c_t["M"], ss_c_t["M"]
        ))

  # TODO
#  fn_out = "%s/rocksdb-sst-creation-cnt-by-reasons-by-time" % Conf.GetOutDir()
#  with open(fn_out, "w") as fo:
#    fo.write("\n")
#  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
#  return fn_out
