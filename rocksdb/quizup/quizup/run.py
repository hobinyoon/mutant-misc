#!/usr/bin/env python

import base64
import datetime
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
  parser.add_option("--job_id", help="Job ID. Unique to an EC2 instance")
  parser.add_option("--fast_dev_path", help="Fast dev path")
  parser.add_option("--slow_dev1_path", help="Slow dev1 path")
  parser.add_option("--slow_dev2_path", help="Slow dev1 path")
  parser.add_option("--slow_dev3_path", help="Slow dev1 path")
  parser.add_option("--db_path", help="DB path")
  parser.add_option("--init_db_to_90p_loaded", help="Upload result to S3")
  parser.add_option("--evict_cached_data", default="true", help="Evict cached data")
  parser.add_option("--memory_limit_in_mb", default=0, help="Memory limit in MB. 0 for unlimited.")
  parser.add_option("--upload_result_to_s3", action='store_true', help="Upload result to S3")

  parser.add_option("--exp_desc", help="Base64-encoded experiment description")

  parser.add_option("--cache_filter_index_at_all_levels", help="Cache metadata")
  parser.add_option("--monitor_temp", help="Monitor temperature")
  parser.add_option("--migrate_sstables", help="Migrate SSTables")
  parser.add_option("--sst_ott", help="SSTable organization temperature threshold")
  parser.add_option("--organize_L0_sstables", help="Organize L0 SSTables")
  parser.add_option("--121x_speed_replay", help="1x-2x-1x speed replay")
  parser.add_option("--pid_params", help="PID controller parameters")

  parser.add_option("--workload_start_from", help="Where the workload data is to be played. In percentage.")
  parser.add_option("--workload_stop_at", help="Where the workload data is to be played. In percentage.")
  parser.add_option("--simulation_time_dur_in_sec", help="Simulation time duration.")

  parser.add_option("--record_size", help="Record size")

  parser.add_option("--sla_admin", help="Run SLA Admin")
  parser.add_option("--lat_hist_q_size", help="Latency history queue size")
  parser.add_option("--sst_ott_adj_ranges", help="sst_ott adjustment ranges")

  parser.add_option("--extra_reads", help="Req extra reads")
  parser.add_option("--xr_queue_size", help="XR queue size")
  parser.add_option("--xr_iops", help="XR IOPS")
  parser.add_option("--xr_gets_per_key", help="XR gets per key")

  (options, args) = parser.parse_args()
  if len(args) != 0:
    parser.error("wrong number of arguments")
  Cons.P(pprint.pformat(options))

  signal.signal(signal.SIGINT, sigint_handler)

  with Cons.MT("Building ..."):
    if socket.gethostname() == "node3":
      Util.RunSubp("make -j")
    else:
      Util.RunSubp("make -j16")

  # Set fast dev paths, e.g., "/mnt/local-ssd1/rocksdb-data" and
  # symlink ~/work/rocksdb-data to it
  if hasattr(options, "fast_dev_path"):
    with Cons.MT("Setting up fast_dev_path:", print_time=False):
      if socket.gethostname() == "node3":
        pass
      else:
        # We don't delete content in the fast_dev to save the rsync time.
        Util.RunSubp("sudo mkdir -p %s && sudo chown ubuntu %s" % (options.fast_dev_path, options.fast_dev_path))
        Util.RunSubp("rm %s/work/rocksdb-data || true" % os.path.expanduser("~"))
        Util.RunSubp("ln -s %s %s/work/rocksdb-data" % (options.fast_dev_path, os.path.expanduser("~")))

  if options.db_path is None:
    raise RuntimeError("Unexpected")

  if options.init_db_to_90p_loaded.lower() == "true":
    with Cons.MT("Loading the 90% loaded DB ..."):
      # Use the local copy on mjolnir
      if socket.gethostname() == "node3":
        Util.RunSubp("rsync -av -e ssh --delete ~/work/rocksdb-data/quizup-90p-loaded/quizup localhost:work/rocksdb-data/")
      else:
        # The experiment is run on us-east-1. Don't bother with synching with
        # the other regions for now. It's a huge amount of traffic and "aws s3
        # sync" doesn't provide a way. You need "aws s3 cp" as well for
        # uploading the result later on.
        Util.RunSubp("aws s3 sync --delete s3://rocksdb-data/quizup-90p-loaded %s" % options.db_path)
  else:
    # Delete existing data
    if socket.gethostname() == "node3":
      Util.RunSubp("rm -rf %s || true" % options.db_path)
    else:
      Util.RunSubp("sudo rm -rf %s || true" % options.db_path)

  # Set slow dev paths
  if socket.gethostname() == "node3":
    # No need for this on mjolnir
    pass
  else:
    for i in range(1, 4):
      attr_name = "slow_dev%d_path" % i
      if not hasattr(options, attr_name):
        continue
      slow_dev_path = getattr(options, attr_name)
      if slow_dev_path is not None:
        with Cons.MT("Setting up slow_dev%d_path:" % i, print_time=False):
          Util.RunSubp("sudo rm -rf %s || true" % slow_dev_path)
          Util.RunSubp("sudo mkdir -p %s && sudo chown ubuntu %s" % (slow_dev_path, slow_dev_path))
          # Let RocksDB use the slow devices directly. This symlink approach
          # doesn't work when the database doesn't exist yet.
          #Util.RunSubp("rm %s/work/rocksdb-data/quizup/t%d || true" % (os.path.expanduser("~"), i))
          #Util.RunSubp("ln -s %s %s/work/rocksdb-data/quizup/t%d" % (slow_dev_path, os.path.expanduser("~"), i))

  if options.evict_cached_data.lower() == "true":
    if socket.gethostname() == "node3":
      pass
    else:
      _EvictCache()

  Dstat.Restart()

  # Construct args for quizup. Not all arguments to this script needs to be passed.
  args0 = []
  for k in [ \
      "db_path" \
      , "slow_dev1_path", "slow_dev2_path", "slow_dev3_path" \
      , "cache_filter_index_at_all_levels" \
      , "monitor_temp" \
      , "migrate_sstables" \
      , "workload_start_from", "workload_stop_at" \
      , "simulation_time_dur_in_sec" \
      , "sst_ott" \
      , "organize_L0_sstables" \
      , "121x_speed_replay" \
      , "pid_params" \
      , "record_size" \
      , "sla_admin" \
      , "lat_hist_q_size" \
      , "sst_ott_adj_ranges" \
      , "extra_reads" \
      , "xr_queue_size" \
      , "xr_iops" \
      , "xr_gets_per_key" \
      ]:
    if (hasattr(options, k)) and (getattr(options, k) is not None):
      args0.append("--%s=%s" % (k, getattr(options, k)))
  cmd = "stdbuf -i0 -o0 -e0 ./quizup %s" % " ".join(args0)

  if options.memory_limit_in_mb == 0:
    Util.RunSubp("LD_LIBRARY_PATH=%s/work/mutant/rocksdb %s" \
        % (os.path.expanduser("~"), cmd), shell=True, gen_exception=False)
  else:
    fn_cgconfig = None
    if socket.gethostname() == "node3":
      # Different user name on mjolnir
      fn_cgconfig = "%s/cgconfig-mjolnir.conf" % os.path.dirname(__file__)
    else:
      fn_cgconfig = "%s/cgconfig.conf" % os.path.dirname(__file__)
    Util.RunSubp("sed -i 's/" \
        "^    memory\.limit_in_bytes = .*" \
        "/    memory\.limit_in_bytes = %d;" \
        "/g' %s" % (int(float(options.memory_limit_in_mb) * 1024 * 1024), fn_cgconfig))
    Util.RunSubp("sudo cgconfigparser -l %s" % fn_cgconfig)
    Util.RunSubp("LD_LIBRARY_PATH=%s/work/mutant/rocksdb cgexec -g memory:small_mem %s" \
        % (os.path.expanduser("~"), cmd), shell=True, gen_exception=False)

  Dstat.Stop()

  # Draw attention if there is any WARN or ERROR in the RocksDB log
  CheckRocksDBLog()

  AppendAllOptionsToClientLogFileAndZip(options)

  UploadToS3(options.job_id)


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
