#!/usr/bin/env python

import base64
import datetime
import json
import optparse
import os
import pprint
import re
import signal
import socket
import subprocess
import sys
import yaml
import zlib

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib" % os.path.expanduser("~"))
import Ec2Util


def sigint_handler(signal, frame):
  pass


def main(argv):
  if len(argv) != 2:
    raise RuntimeError("Unexpected")

  signal.signal(signal.SIGINT, sigint_handler)

  params = json.loads(zlib.decompress(base64.b64decode(argv[1])))
  #Cons.P(pprint.pformat(params))

  # TODO: Not sure if you will need this for now
  ## Set fast dev paths, e.g., "/mnt/local-ssd1/rocksdb-data" and symlink ~/work/rocksdb-data to it
  #with Cons.MT("Setting up fast_dev_path:", print_time=False):
  #  if socket.gethostname() == "node3":
  #    pass
  #  else:
  #    Cons.P(params["fast_dev_path"])
  #    sys.exit(0)
  #    # We don't delete content in the fast_dev to save the rsync time.
  #    Util.RunSubp("sudo mkdir -p %s && sudo chown ubuntu %s" % (params["fast_dev_path"], params["fast_dev_path"]))
  #    Util.RunSubp("rm %s/work/rocksdb-data || true" % os.path.expanduser("~"))
  #    Util.RunSubp("ln -s %s %s/work/rocksdb-data" % (params["fast_dev_path"], os.path.expanduser("~")))

  for r in params["runs"]:
    if "load" in r:
      YcsbLoad(params, r)

    if r["run"]["evict_cached_data"].lower() == "true":
      if socket.gethostname() == "node3":
        pass
      else:
        _EvictCache()

    Dstat.Restart()
    YcsbRun(params, r)
    Dstat.Stop()

  UploadCloudInitLog()


_dn_log_root = None
_dn_ycsb = "%s/work/mutant/YCSB" % os.path.expanduser("~")
_dn_log_rocksdb = None
_dn_log_root_ycsb = None

# Just a note: The DB could be preloaded to save time. Too much optimization. Not needed for now.
def YcsbLoad(params, r):
  with Cons.MT("Loading the YCSB workload ..."):
    global _dn_log_root
    _dn_log_root = "%s/ycsb/%s" % (Conf.GetDir("log_archive_dn"), Ec2Util.JobId())

    global _dn_log_root_ycsb
    _dn_log_root_ycsb = "%s/ycsb" % _dn_log_root
    Util.MkDirs(_dn_log_root_ycsb)

    global _dn_log_rocksdb
    _dn_log_rocksdb = "%s/rocksdb" % _dn_log_root
    Util.MkDirs(_dn_log_rocksdb)

    if "unzip-preloaded-db" in r["load"]:
      cmd = "aws s3 sync --delete s3://rocksdb-data/%s %s" % (r["load"]["unzip-preloaded-db"], params["db_path"])
      Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
    else:
      # Delete existing data
      if socket.gethostname() == "node3":
        Util.RunSubp("rm -rf %s || true" % params["db_path"])
      else:
        Util.RunSubp("sudo rm -rf %s || true" % params["db_path"])

      ycsb_params = \
          " -s" \
          " -P workloads/workload%s" \
          " -p rocksdb.dir=%s" \
          " -threads 100" \
          " -p status.interval=1" \
          " -p fieldcount=10" \
          " -p fieldlength=100" \
          " %s" \
          % (params["workload_type"], params["db_path"], r["load"]["ycsb_params"])

      # -P file        Specify workload file
      # -cp path       Additional Java classpath entries
      # -jvm-args args Additional arguments to the JVM
      # -p key=value   Override workload property
      # -s             Print status to stderr
      # -target n      Target ops/sec (default: unthrottled)
      # -threads n     Number of client threads (default: 1)

      # The ycsb log directory contains 2 files when the load phase is included. 1, otherwise.
      cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")[:-3]
      fn_ycsb_log = "%s/%s-%s" % (_dn_log_root_ycsb, cur_datetime, params["workload_type"])
      cmd = "cd %s && bin/ycsb load rocksdb %s > %s 2>&1" % (_dn_ycsb, ycsb_params, fn_ycsb_log)
      Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
      Cons.P("Created %s %d" % (fn_ycsb_log, os.path.getsize(fn_ycsb_log)))
      Util.RunSubp("pbzip2 -k %s" % fn_ycsb_log)
      UploadToS3("%s.bz2" % fn_ycsb_log)

      # Archive rocksdb log
      fn1 = "%s/%s" % (_dn_log_rocksdb, cur_datetime)
      cmd = "cp %s/LOG %s" % (params["db_path"], fn1)
      Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
      Util.RunSubp("pbzip2 -k %s" % fn1)
      UploadToS3("%s.bz2" % fn1)
      CheckRocksDBLog(fn1)


_ycsb_run_dt = None

def YcsbRun(params, r):
  global _ycsb_run_dt
  _ycsb_run_dt = datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")[:-3]
  fn_ycsb_log = "%s/%s-%s" % (_dn_log_root_ycsb, _ycsb_run_dt, params["workload_type"])

  ycsb_params = \
      " -s" \
      " -P workloads/workload%s" \
      " -p rocksdb.dir=%s" \
      " -p measurementtype=raw" \
      " -p measurement.raw.output_file=/tmp/ycsb-lat-raw" \
      " -threads 100" \
      " -p status.interval=1" \
      " -p fieldcount=10" \
      " -p fieldlength=100" \
      " -p readproportion=0.95" \
      " -p insertproportion=0.05" \
      " %s" \
      % (params["workload_type"], params["db_path"], r["run"]["ycsb_params"])

  cmd0 = "cd %s && bin/ycsb run rocksdb %s > %s 2>&1" % (_dn_ycsb, ycsb_params, fn_ycsb_log)
  cmd1 = "bin/ycsb run rocksdb %s > %s 2>&1" % (ycsb_params, fn_ycsb_log)

  # TODO: other than limiting the memory here, you will have to tell JVM the same as well.
  if ("memory_limit_in_mb" in r) and (r["memory_limit_in_mb"] != 0):
    fn_cgconfig = None
    if socket.gethostname() == "node3":
      # Different user name on mjolnir
      fn_cgconfig = "%s/cgconfig-mjolnir.conf" % os.path.dirname(__file__)
    else:
      fn_cgconfig = "%s/cgconfig.conf" % os.path.dirname(__file__)
    Util.RunSubp("sed -i 's/" \
        "^    memory\.limit_in_bytes = .*" \
        "/    memory\.limit_in_bytes = %d;" \
        "/g' %s" % (int(float(r["run"]["memory_limit_in_mb"]) * 1024 * 1024), fn_cgconfig))
    Util.RunSubp("sudo cgconfigparser -l %s" % fn_cgconfig)
    Util.RunSubp("cd %s && cgexec -g memory:small_mem %s" % (_dn_ycsb, cmd1)
        , measure_time=True, shell=True, gen_exception=False)
  else:
    Util.RunSubp(cmd0, measure_time=True, shell=True, gen_exception=False)

  Cons.P("Created %s %d" % (fn_ycsb_log, os.path.getsize(fn_ycsb_log)))
  Util.RunSubp("pbzip2 -k %s" % fn_ycsb_log)
  UploadToS3("%s.bz2" % fn_ycsb_log)

  # Archive rocksdb log
  fn1 = "%s/%s" % (_dn_log_rocksdb, _ycsb_run_dt)
  cmd = "cp %s/LOG %s" % (params["db_path"], fn1)
  Util.RunSubp(cmd, measure_time=True, shell=True, gen_exception=False)
  Util.RunSubp("pbzip2 -k %s" % fn1)
  UploadToS3("%s.bz2" % fn1)
  CheckRocksDBLog(fn1)


def _EvictCache():
  with Cons.MT("Drop caches ..."):
    # We drop all rather than cherry picking
    Util.RunSubp("sudo sh -c \"echo 3 >/proc/sys/vm/drop_caches\"")


class Dstat:
  cur_datetime = None
  dn_dstat = None

  @staticmethod
  def Restart():
    with Cons.MT("Restarting dstat ...", print_time=False):
      Dstat._Stop()
      Dstat.dn_dstat = "%s/dstat" % _dn_log_root
      Util.MkDirs(Dstat.dn_dstat)

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

      Dstat.cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")[:-3]
      Cons.P(Dstat.cur_datetime)

      # Run dstat as a daemon
      fn_out = "%s/%s.csv" % (Dstat.dn_dstat, Dstat.cur_datetime)
      cmd = "dstat -tcdnrmy -D %s --output %s" % (",".join(devs), fn_out)
      Util.RunDaemon(cmd)

  @staticmethod
  def Stop():
    with Cons.MT("Stopping dstat ...", print_time=False):
      Dstat._Stop()

    # Change the current dstat log file name to match that of the last ycsb log datetime
    if Dstat.cur_datetime is not None:
      with Cons.MT("Renaming the log file and zipping ..."):
        global _ycsb_run_dt
        if _ycsb_run_dt is None:
          raise RuntimeError("Unexpected")
        if _ycsb_run_dt < Dstat.cur_datetime:
          raise RuntimeError("Unexpected")
        fn0 = "%s/%s.csv" % (Dstat.dn_dstat, Dstat.cur_datetime)
        fn1 = "%s/%s.csv" % (Dstat.dn_dstat, _ycsb_run_dt)
        Cons.P("renaming %s to %s" % (fn0, fn1))
        os.rename(fn0, fn1)
        Util.RunSubp("pbzip2 -k %s" % fn1)
        UploadToS3("%s.bz2" % fn1)

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


# Draw attention if there is any WARN or ERROR in the RocksDB log
def CheckRocksDBLog(fn):
  warning_lines = []
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


def UploadCloudInitLog():
  dn_ci_log = "%s/cloud-init" % _dn_log_root
  Util.MkDirs(dn_ci_log)
  Util.RunSubp("cp /var/log/cloud-init.log %s" % dn_ci_log)
  Util.RunSubp("cp /var/log/cloud-init-output.log %s" % dn_ci_log)
  Util.RunSubp("cp /mnt/local-ssd0/mutant/log/%s/cloud-init %s/local-ssd-cloud-init" % (Ec2Util.JobId(), dn_ci_log))
  Util.RunSubp("cd %s && (tar cf - cloud-init | pbzip2 > cloud-init.tar.bz2)" % _dn_log_root)
  UploadToS3("%s/cloud-init.tar.bz2" % _dn_log_root)


def UploadToS3(fn):
  if not fn.startswith(Conf.GetDir("log_archive_dn")):
    raise RuntimeError("Unexpected fn %s" % fn)
  # local: /mnt/local-ssd0/mutant/log/
  # s3: mutant-log/
  fn_s3 = "s3://mutant-log/%s" % fn[len(Conf.GetDir("log_archive_dn")) + 1:]
  Util.RunSubp("aws s3 cp %s %s > /dev/null" % (fn, fn_s3))


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
  sys.exit(main(sys.argv))
