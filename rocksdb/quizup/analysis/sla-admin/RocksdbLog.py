import datetime
import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import SimTime

def GetSlaAdminLog(fn, exp_dt):
  if not os.path.exists(fn):
    fn_zipped = "%s.7z" % fn
    if not os.path.exists(fn_zipped):
      raise RuntimeError("Unexpected: %s" % fn)
    Util.RunSubp("cd %s && 7z e %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
  if not os.path.exists(fn):
    raise RuntimeError("Unexpected")

  fn_out = "%s/rocksdb-sla-admin-%s" % (Conf.GetDir("output_dir"), exp_dt)
  pid_params = None

  with open(fn) as fo, open(fn_out, "w") as fo_out:
    fmt = "%12s %7.2f %8.2f %10.6f %3d %3d %3d %3d"
    header = Util.BuildHeader(fmt, "ts cur_latency adj new_sst_ott" \
        " num_ssts_in_fast_dev num_ssts_in_slow_dev num_ssts_should_be_in_fast_dev num_ssts_should_be_in_slow_dev")
    i = 0
    for line in fo:
      line = line.strip()
      if "mutant_sla_admin_init" in line:
        #Cons.P(line)
        # 2017/09/04-14:38:46.191160 7f084ccf9700 EVENT_LOG_v1 {"time_micros": 1504535926190841, "mutant_sla_admin_init": {"target_value":
        # 19, "p": 1, "i": 0, "d": 0}}
        mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
        j = json.loads(mo.group("json"))
        j1 = j["mutant_sla_admin_init"]
        pid_params = j1
        fo_out.write("# target_latency: %s\n" % j1["target_value"])
        fo_out.write("# k_p: %s\n" % j1["p"])
        fo_out.write("# k_i: %s\n" % j1["i"])
        fo_out.write("# k_d: %s\n" % j1["d"])
        fo_out.write("#\n")
      elif "mutant_sla_admin_adjust" in line:
        #Cons.P(line)
        # 2017/09/04-14:38:46.363976 7f07f8450700 EVENT_LOG_v1 {"time_micros": 1504535926363296, "mutant_sla_admin_adjust": {"cur_lat":
        # 21.535, "dt": 0, "p": -2.53497, "i": 0, "d": 0, "adj": -2.53497, "sst_ott": 7.46503, "sst_status": "1209:2:17.113:0:0
        # 1316:2:66.572:0:0 ...", "num_ssts_in_fast_dev": 126, "num_ssts_in_slow_dev": 6, "num_ssts_should_be_in_fast_dev": 132,
        # "num_ssts_should_be_in_slow_dev": 0}}
        mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
        try:
          j = json.loads(mo.group("json"))
        except ValueError as e:
          # This happens when the log file is not finialized.
          Cons.P("Exception: %s" % e)
          Cons.P("  fn: %s" % fn)
          Cons.P("  time_micros: %s" % j["time_micros"])
          Cons.P("  Ignoring ...")
          continue

        # time_micros is in local time. ts seems to be in UTC. Quizup ts is in UTC.
        #ts = datetime.datetime.fromtimestamp(int(j["time_micros"]) / 1000000.0)
        ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
        ts_rel = ts - SimTime.SimulationTimeBegin()

        j1 = j["mutant_sla_admin_adjust"]

        #dt = float(j1["dt"])
        # Only the first one is 0. Taken care of by the PID controller.

        if i % 40 == 0:
          fo_out.write(header + "\n")
        fo_out.write((fmt + "\n") % (
          str(ts_rel)[:11]
          , j1["cur_lat"]
          , j1["adj"]
          , j1["sst_ott"]
          , j1["num_ssts_in_fast_dev"]
          , j1["num_ssts_in_slow_dev"]
          , j1["num_ssts_should_be_in_fast_dev"]
          , j1["num_ssts_should_be_in_slow_dev"]
          ))
        i += 1
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return (fn_out, pid_params)