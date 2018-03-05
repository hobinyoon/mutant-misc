#!/usr/bin/env python

import base64
import datetime
import json
import optparse
import os
import pprint
import re
import socket
import subprocess
import sys
import time
import types
import yaml
import zlib

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib" % os.path.expanduser("~"))
import BotoClient

_cur_datetime = None
_latest_client_log_dt = None

import signal

def sigint_handler(signal, frame):
  pass


def main():
  parser = optparse.OptionParser(usage="usage: %prog [options]",
      version="%prog 0.1")
  parser.add_option("--encoded_params", help="Encoded parameters")

  (options, args) = parser.parse_args()
  if len(args) != 0:
    parser.error("wrong number of arguments")
  #Cons.P(pprint.pformat(options))

  signal.signal(signal.SIGINT, sigint_handler)

  params = json.loads(zlib.decompress(base64.b64decode(options.encoded_params)))
  # Cons.P(pprint.pformat(params))
  #
  # {u'cache_filter_index_at_all_levels': u'false',
  #     u'db_path': u'/mnt/local-ssd1/rocksdb-data/quizup',
  #     u'db_stg_devs': [[u'/mnt/local-ssd0/rocksdb-data/ycsb/t0', 0.528],
  #       [u'/mnt/ebs-st1/rocksdb-data-t1', 0.045]],
  #     u'evict_cached_data': u'true',
  #     u'exp_desc': u'Mutant_QuizUp',
  #     u'memory_limit_in_mb': 5120.0,
  #     u'migrate_sstables': u'true',
  #     u'migration_resistance': 0.05,
  #     u'monitor_temp': u'true',
  #     u'record_size': 5000,
  #     u'simulation_time_dur_in_sec': 600,
  #     u'target_cost': 0.4,
  #     u'use_90p_loaded_db': u'false',
  #     u'workload_time_range': [0.0, 0.9]}

  with Cons.MT("Building ..."):
    Util.RunSubp("make -j16")

  if ("use_90p_loaded_db" in params) and (params["use_90p_loaded_db"].lower() == "true"):
    raise RuntimeError("Implement!")
    # cmd = "aws s3 sync --delete s3://rocksdb-data/%s %s" % (r["load"]["use_90p_loaded_db"][0], params["db_path"])
    # # aws s3 sync fails sometimes when pounded with requests and it seems that it doesn't tell you whether it succeeded or not.
    # #   Repeat many times. It fixed the issue.
    # #   A better approach would be running a checksum. Oh well.
    # for i in range(5):
    #   Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
    # if 2 <= len(r["load"]["use_90p_loaded_db"]):
    #   cmd = "aws s3 sync --delete s3://rocksdb-data/%s %s" % (r["load"]["use_90p_loaded_db"][1], params["db_stg_devs"][1][0])
    #   for i in range(5):
    #     Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
    # Util.RunSubp("sync", measure_time=True, shell=True, gen_exception=False)

    # # Re-create the directories when a preloaded DB is not specified.
    # paths = params["db_stg_devs"]
    # for i in range(len(r["load"]["use_90p_loaded_db"]), len(paths)):
    #   Util.RunSubp("rm -rf %s || true" % paths[i][0])
    #   Util.MkDirs(paths[i][0])

  # Load the database from the scratch
  else:
    # Delete existing data
    Util.RunSubp("sudo rm -rf %s || true" % params["db_path"])

    for p in params["db_stg_devs"]:
      Util.RunSubp("rm -rf %s || true" % p[0])
      Util.MkDirs(p[0])

    # One experiment per machine instance. We don't do multiple experiments, since it's bad for the EBS rate limiting.

    if False:
      # The ycsb log directory contains 2 files when the load phase is included. 1, otherwise.
      cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")[:-3]
      fn_ycsb_log = "%s/%s-%s" % (_dn_log_root_ycsb, cur_datetime, params["workload_type"])
      cmd = "cd %s && bin/ycsb load rocksdb %s -m %s > %s 2>&1" % (_dn_ycsb, ycsb_params, mutant_options, fn_ycsb_log)
      Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
      Cons.P("Created %s %d" % (fn_ycsb_log, os.path.getsize(fn_ycsb_log)))
      # No need to upload these to S3
      #Util.RunSubp("pbzip2 -k %s" % fn_ycsb_log)
      #UploadToS3("%s.bz2" % fn_ycsb_log)

      # Archive rocksdb log
      fn1 = "%s/%s" % (_dn_log_rocksdb, cur_datetime)
      cmd = "cp %s/LOG %s" % (params["db_path"], fn1)
      Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
      #Util.RunSubp("pbzip2 -k %s" % fn1)
      #UploadToS3("%s.bz2" % fn1)
      CheckRocksDBLog(fn1)

  if params["evict_cached_data"].lower() == "true":
    _EvictCache()

  Dstat.Restart()

  cmd = "stdbuf -i0 -o0 -e0 ./quizup --encoded_params=%s" % options.encoded_params

  if params["memory_limit_in_mb"] == 0:
    Util.RunSubp("LD_LIBRARY_PATH=%s/work/mutant/rocksdb %s" \
        % (os.path.expanduser("~"), cmd), shell=True, gen_exception=False)
  else:
    fn_cgconfig = "%s/cgconfig.conf" % os.path.dirname(__file__)
    Util.RunSubp("sed -i 's/" \
        "^    memory\.limit_in_bytes = .*" \
        "/    memory\.limit_in_bytes = %d;" \
        "/g' %s" % (int(float(params["memory_limit_in_mb"]) * 1024 * 1024), fn_cgconfig))
    Util.RunSubp("sudo cgconfigparser -l %s" % fn_cgconfig)
    Util.RunSubp("LD_LIBRARY_PATH=%s/work/mutant/rocksdb cgexec -g memory:small_mem %s" \
        % (os.path.expanduser("~"), cmd), shell=True, gen_exception=False)

  Dstat.Stop()

  # Draw attention if there is any WARN or ERROR in the RocksDB log
  CheckRocksDBLog()

  if ("upload_result_to_s3" in params) and (params["upload_result_to_s3"].lower() == "true"):
    AppendAllOptionsToClientLogFileAndZip(params)
    UploadToS3(params["job_id"])


def _EvictCache():
  with Cons.MT("Drop caches ..."):
      Util.RunSubp("sudo sh -c \"echo 3 >/proc/sys/vm/drop_caches\"")

  if False:
    # Evict the DB data files from cache
    with Cons.MT("Evicting DB data ..."):
      Util.RunSubp("%s/work/vmtouch/vmtouch -e %s" % (os.path.expanduser("~"), Conf.GetDir("db_path")))

    # Evict the input data files from cache so that the read IO is consistent
    # throughput the experiment.
    # Caching them would have been nice, but you can do it only when you limit
    # the memory smaller than 3.4 GB (= 15 (total ram) - 0.4 (for the OS) - 11.2
    # (the 100% quizup data size)
    evict = True
    if evict:
      with Cons.MT("Evicting workload data ..."):
        Util.RunSubp("%s/work/vmtouch/vmtouch -e %s" % (os.path.expanduser("~"), Conf.GetDir("workload_dir")))
    else:
      with Cons.MT("Caching workload data ..."):
        Util.RunSubp("%s/work/vmtouch/vmtouch -t %s" % (os.path.expanduser("~"), Conf.GetDir("workload_dir")))


class Dstat:
  @staticmethod
  def Restart():
    with Cons.MT("Restarting dstat ...", print_time=False):
      Dstat._Stop()

      dn = "%s/dstat" % Conf.GetDir("log_archive_dn")
      Util.MkDirs(dn)

      # Get a list of all block devices
      devs = []
      for f in os.listdir("/dev"):
        mo = None
        if socket.gethostname() == "node3":
          mo = re.match(r"sd\w$", f)
        else:
          mo = re.match(r"xvd\w$", f)
        if mo is not None:
          devs.append(f)

      global _cur_datetime
      _cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")[:-3]
      Cons.P(_cur_datetime)

      # Run dstat as a daemon
      fn_out = "%s/%s.csv" % (dn, _cur_datetime)
      cmd = "dstat -tcdnrmy -D %s --output %s" % (",".join(devs), fn_out)
      Util.RunDaemon(cmd)

  @staticmethod
  def Stop():
    with Cons.MT("Stopping dstat ...", print_time=False):
      Dstat._Stop()

    # Change the current dstat log file name to the simulation_time_begin of
    # the simulator.
    if _cur_datetime is not None:
      with Cons.MT("Renaming the log file and zipping ..."):
        dn_client = "%s/quizup" % Conf.GetDir("log_archive_dn")
        global _latest_client_log_dt
        _latest_client_log_dt = None
        for f in os.listdir(dn_client):
          mo = re.match(r"(?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)$", f)
          if mo is not None:
            if _latest_client_log_dt is None:
              _latest_client_log_dt = mo.group("dt")
            else:
              _latest_client_log_dt = max(_latest_client_log_dt, mo.group("dt"))
        # There should be a client log file whose dt is bigger than
        # _cur_datetime
        if _latest_client_log_dt <= _cur_datetime:
          raise RuntimeError("Unexpected")
        fn0 = "%s/dstat/%s.csv" % (Conf.GetDir("log_archive_dn"), _cur_datetime)
        fn1 = "%s/dstat/%s.csv" % (Conf.GetDir("log_archive_dn"), _latest_client_log_dt)
        Cons.P("renaming %s to %s" % (fn0, fn1))
        os.rename(fn0, fn1)
        Util.RunSubp("7z a -mx %s.7z %s" % (fn1, fn1))


  @staticmethod
  def _Stop():
    cmd = "ps -e -o pid,ppid,user,args"
    lines = Util.RunSubp(cmd, print_cmd=False, print_output=False)
    #Cons.P(lines)
    pids = []
    for line in lines.split("\n"):
      line = line.strip()
      if "dstat" not in line:
        continue
      if "csv" not in line:
        continue

      # Get the second-level processes, skipping the root-level ones.
      t = re.split(" +", line)
      if t[1] == "1":
        continue
      pids.append(t[0])
      #Cons.P("[%s]" % line)

    if len(pids) > 0:
      #Cons.P("[%s]" % " ".join(pids))
      Util.RunSubp("kill %s" % " ".join(pids))

      # Make sure each of the processes has terminated
      for pid in pids:
        cmd = "kill -0 %s" % pid
        while True:
          r = 0
          with open(os.devnull, "w") as devnull:
            r = subprocess.Popen(cmd, shell=True, stdin=devnull, stdout=devnull, stderr=devnull)
          if r != 0:
            Cons.P("Process %s has terminated" % pid)
            break
          time.sleep(0.1)


def CheckRocksDBLog():
  global _latest_client_log_dt
  if _latest_client_log_dt is None:
    raise RuntimeError("Unexpected")

  warning_lines = []
  fn = "%s/rocksdb/%s" % (Conf.GetDir("log_archive_dn"), _latest_client_log_dt)
  with open(fn) as fo:
    line_cnt = 0
    line_no_last_dumping_stat_0 = None
    line_no_last_dumping_stat_1 = None
    line_no_last_dumping_stat_2 = None
    for line in fo:
      line = line.strip()
      line_cnt += 1
      # 2016/12/27-05:09:20.198030 7fb26d436700 [WARN] ------- DUMPING STATS -------
      mo = re.match(r".+ \[WARN\] ------- DUMPING STATS -------$", line)
      if mo is not None:
        line_no_last_dumping_stat_0 = line_cnt
        #Cons.P(line)
        continue

      # This follows right after or 2 lines after the above one
      #
      # 2016/12/27-04:59:04.127228 7fb24d7fa700 [WARN]
      # ** Compaction Stats [default] **
      mo = re.match(r".+ \[WARN\]$", line)
      if mo is not None:
        if line_cnt - line_no_last_dumping_stat_0 <= 2:
          #Cons.P(line)
          pass
        else:
          Cons.P("Unexpected: %s" % line)
        continue

      mo = re.match(r".+ \[(WARN|ERROR)\].*", line)
      if mo is not None:
        warning_lines.append(line)
        #Cons.P("Unexpected: %s" % line)
  Cons.P("RocksDB warnings or errors:")
  for l in warning_lines:
    Cons.P("  %s" % l)


def AppendAllOptionsToClientLogFileAndZip(options):
  global _latest_client_log_dt
  if _latest_client_log_dt is None:
    raise RuntimeError("Unexpected")

  fn = "%s/quizup/%s" % (Conf.GetDir("log_archive_dn"), _latest_client_log_dt)
  with open(fn, "a") as fo:
    fo.write("# Quizup run script options: %s\n" % pprint.pformat(options))
    fo.write("# Quizup run script options.desc: %s\n" % (base64.b64decode(options.exp_desc) if options.exp_desc is not None else ""))
  Util.RunSubp("7z a -mx %s.7z %s" % (fn, fn))


def UploadToS3(job_id):
  global _latest_client_log_dt
  if _latest_client_log_dt is None:
    raise RuntimeError("Unexpected")

  fn = "quizup/%s.7z" % (_latest_client_log_dt)
  fn_local = "%s/work/mutant/misc/rocksdb/log/%s" % (os.path.expanduser("~"), fn)
  Util.RunSubp("aws s3 cp %s s3://mutant-log/quizup/%s/%s" % (fn_local, job_id, fn))

  fn = "dstat/%s.csv.7z" % (_latest_client_log_dt)
  fn_local = "%s/work/mutant/misc/rocksdb/log/%s" % (os.path.expanduser("~"), fn)
  Util.RunSubp("aws s3 cp %s s3://mutant-log/quizup/%s/%s" % (fn_local, job_id, fn))

  fn = "rocksdb/%s.7z" % (_latest_client_log_dt)
  fn_local = "%s/work/mutant/misc/rocksdb/log/%s" % (os.path.expanduser("~"), fn)
  Util.RunSubp("aws s3 cp %s s3://mutant-log/quizup/%s/%s" % (fn_local, job_id, fn))


class Conf:
  _doc = None
  _init = False

  @staticmethod
  def _Init():
    if Conf._init:
      return
    with open("%s/config.yaml" % os.path.dirname(__file__), "r") as f:
      Conf._doc = yaml.load(f)
    Conf._init = True

  @staticmethod
  def Get(k):
    Conf._Init()
    return Conf._doc[k]

  @staticmethod
  def GetDir(k):
    Conf._Init()
    return Conf._doc[k].replace("~", os.path.expanduser("~"))


if __name__ == "__main__":
  sys.exit(main())
