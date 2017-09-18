import collections
import datetime
import json
import os
import pprint
import re
import sys

import Queue

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import SimTime

def ParseLog(fn, exp_dt):
  with Cons.MT("Parsing RocksDB log %s ..." % fn):
    return _ParseLog(fn, exp_dt)


def _ParseLog(fn, exp_dt):
  if not os.path.exists(fn):
    fn_zipped = "%s.7z" % fn
    if not os.path.exists(fn_zipped):
      raise RuntimeError("Unexpected: %s" % fn)
    Util.RunSubp("cd %s && 7z e %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
  if not os.path.exists(fn):
    raise RuntimeError("Unexpected")

  fn_out = "%s/rocksdb-sla-admin-%s" % (Conf.GetDir("output_dir"), exp_dt)
  pid_params = None
  num_sla_adj = 0
  last_lines_mutant_table_acc_cnt = Queue.Queue()

  with open(fn) as fo, open(fn_out, "w") as fo_out:
    # {u'num_ssts_should_be_in_slow_dev': 0, u'sst_ott': 0.005, u'num_ssts_in_slow_dev': 0, u'num_ssts_in_fast_dev': 0,
    # u'num_ssts_should_be_in_fast_dev': 0, u'cur_lat': 5.8963, u'adj_type': u'no_sstable', u'sst_status': u''}
    fmt = "%12s %7.2f %7.2f %7.2f %7.2f %1d" \
        " %6.1f %6.1f" \
        " %8.2f" \
        " %3d %3d %3d %3d" \
        " %28s %10.7f %10.7f"
    header = Util.BuildHeader(fmt, "ts cur_latency lat_ra_all_0 lat_ra_all_1 lat_ra_filtered make_adjustment" \
        " slow_dev_r_iops slow_dev_w_iops" \
        " new_sst_ott" \
        " num_ssts_in_fast_dev num_ssts_in_slow_dev num_ssts_should_be_in_fast_dev num_ssts_should_be_in_slow_dev" \
        " adj_type pid_adj pid_adj1" \
        )

    # Running average including all
    # Running average excluding background SSTable compactions and migrations
    lat_q_all_0 = collections.deque()
    lat_q_all_1 = collections.deque()
    lat_q_filtered = collections.deque()

    i = 0
    for line in fo:
      try:
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

          num_sla_adj += 1

          # time_micros is in local time. ts seems to be in UTC. Quizup ts is in UTC.
          #ts = datetime.datetime.fromtimestamp(int(j["time_micros"]) / 1000000.0)
          ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
          ts_rel = ts - SimTime.SimulationTimeBegin()

          j1 = j["mutant_sla_admin_adjust"]

          if i % 40 == 0:
            fo_out.write(header + "\n")
          i += 1

          make_adjustment = j1["make_adjustment"]
          cur_lat = float(j1["cur_lat"])
          # append() appends to the right. coupled with popleft(), it implements a queue.
          lat_q_all_0.append(cur_lat)
          lat_q_all_1.append(cur_lat)
          if make_adjustment == 1:
            lat_q_filtered.append(cur_lat)

          # Calc the averages of the last n observations
          while 10 < len(lat_q_all_0):
            lat_q_all_0.popleft()
          while 400 < len(lat_q_all_1):
            lat_q_all_1.popleft()
          while 10 < len(lat_q_filtered):
            lat_q_filtered.popleft()
          lat_ra_all_0 = -1
          lat_ra_all_1 = -1
          lat_ra_filtered = -1
          if 0 < len(lat_q_all_0):
            lat_ra_all_0 = sum(lat_q_all_0) / len(lat_q_all_0)
          if 0 < len(lat_q_all_1):
            lat_ra_all_1 = sum(lat_q_all_1) / len(lat_q_all_1)
          if 0 < len(lat_q_filtered):
            lat_ra_filtered = sum(lat_q_filtered) / len(lat_q_filtered)

          # {u'num_ssts_should_be_in_slow_dev': 12, u'make_adjustment': 0, u'slow_dev_r_iops': -1, u'num_ssts_in_slow_dev': 0,
          # u'num_ssts_in_fast_dev': 216, u'num_ssts_should_be_in_fast_dev': 204, u'cur_lat': 424.31, u'sst_ott': 0, u'slow_dev_w_iops':
          # -1, u'sst_status': u'2083:2:1.797:0:0 2257:2:3.057:0:0 2386:3:2.446:0:0 2425:2:2.345:0:0 2455:2:3.060:0:0 2529:2:1.581:0:0
          # ...
          # 3843:1:-1.000:0:1'}

          fo_out.write((fmt + "\n") % (
            str(ts_rel)[:11]
            , cur_lat
            , lat_ra_all_0
            , lat_ra_all_1
            , lat_ra_filtered
            , j1["make_adjustment"]
            , j1["slow_dev_r_iops"]
            , j1["slow_dev_w_iops"]
            , j1["sst_ott"]
            , j1["num_ssts_in_fast_dev"]
            , j1["num_ssts_in_slow_dev"]
            , j1["num_ssts_should_be_in_fast_dev"]
            , j1["num_ssts_should_be_in_slow_dev"]
            , j1["adj_type"] if "adj_type" in j1 else "-"
            , j1["adj"] if "adj" in j1 else 0
            , j1["adj1"] if "adj1" in j1 else 0
            ))
        elif "mutant_table_acc_cnt" in line:
          if 500 <= last_lines_mutant_table_acc_cnt.qsize():
            last_lines_mutant_table_acc_cnt.get_nowait()
          last_lines_mutant_table_acc_cnt.put(line)

      except KeyError as e:
        Cons.P("KeyError: %s fn=%s line=%s" % (e, fn, line))
        sys.exit(1)

  # Checked to see what their access count distribution is like
  if False:
    line = None
    try:
      line = last_lines_mutant_table_acc_cnt.get_nowait()
    except Queue.Empty as e:
      # This happens
      pass
    if line is not None:
      _ParseSstAccCnt(line)

  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return (fn_out, pid_params, num_sla_adj)


def _ParseSstAccCnt(line):
  if line is None:
    raise RuntimeError("Unexpected")

  mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)

  ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
  ts_rel = ts - SimTime.SimulationTimeBegin()
  Cons.P("line ts: %s" % str(ts_rel)[:11])

  j = json.loads(mo.group("json"))
  #Cons.P(j["mutant_table_acc_cnt"]["sst"])
  # 2816:2:1:1.046:0.199 2869:2:1:1.046:0.264 2903:3:2:3.705:0.174 3385:3:2:2.092:1.087 3389:3:3:3.138:1.646 ...
  tokens = j["mutant_table_acc_cnt"]["sst"].split(" ")
  sst_acc_infos = []
  for t in tokens:
    sst_acc_infos.append(SstAccInfo(t))

  sst_acc_infos.sort(key=lambda x: x.temp)

  for ai in sst_acc_infos:
    Cons.P(ai)


class SstAccInfo:
  def __init__(self, t):
    t1 = t.split(":")
    if len(t1) != 5:
      raise RuntimeError("Unexpected: [%s]" % t)
    self.sst_id = int(t1[0])
    self.level = int(t1[1])
    self.acc_cnt = int(t1[2])
    self.temp = float(t1[4])

  def __repr__(self):
    return pprint.pformat(vars(self))
