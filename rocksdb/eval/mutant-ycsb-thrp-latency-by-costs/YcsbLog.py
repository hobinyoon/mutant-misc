import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Stat


def GenDataThrpVsLat():
  fn_out = "%s/mutant-ycsb-thrp-vs-lat-by-costslos" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  # {clst_slo: {target_iops: YcsbLogReader}}
  costslo_tio_ylr = {}

  with Cons.MT("Generating thrp vs lat data file ..."):
    conf_root = Conf.Get("mutant")
    dn_base = conf_root["dn_base"].replace("~", os.path.expanduser("~"))

    for k, v in sorted(conf_root["by_cost_slos"].iteritems()):
      # k: "0.1, 0.1":
      mo = re.match(r"(?P<cost_slo>(\d|.)+), ?(?P<cost_slo_epsilon>(\d|.)+)", k)
      cost_slo = float(mo.group("cost_slo"))
      # This is not used for now
      cost_slo_epsilon = float(mo.group("cost_slo_epsilon"))
      if cost_slo not in costslo_tio_ylr:
        costslo_tio_ylr[cost_slo] = {}

      #Cons.P("%f %f" % (cost_slo, cost_slo_epsilon))
      for target_iops, v1 in sorted(v.iteritems()):
        fn = "%s/%s" % (dn_base, v1["fn"])
        # 01:30:00-04:00:00
        t = v1["time"].split("-")
        time_begin = t[0]
        time_end = t[1]
        # Not sure if you want to parallelize this. This whole thing takes only about 4 secs.
        costslo_tio_ylr[cost_slo][target_iops] = YcsbLogReader(fn, time_begin, time_end)

    conf_root = Conf.Get("rocksdb")
    dn_base = conf_root["dn_base"].replace("~", os.path.expanduser("~"))
    cost_ebsst1   = 0.045
    cost_localssd = 0.528

    cost_slo = cost_localssd
    costslo_tio_ylr[cost_slo] = {}
    for target_iops, v1 in sorted(conf_root["local-ssd"].iteritems()):
      fn = "%s/%s" % (dn_base, v1["fn"])
      t = v1["time"].split("-")
      time_begin = t[0]
      time_end = t[1]
      costslo_tio_ylr[cost_slo][target_iops] = YcsbLogReader(fn, time_begin, time_end)

    cost_slo = cost_ebsst1
    costslo_tio_ylr[cost_slo] = {}
    for target_iops, v1 in sorted(conf_root["ebs-st1"].iteritems()):
      fn = "%s/%s" % (dn_base, v1["fn"])
      t = v1["time"].split("-")
      time_begin = t[0]
      time_end = t[1]
      costslo_tio_ylr[cost_slo][target_iops] = YcsbLogReader(fn, time_begin, time_end)

  with open(fn_out, "w") as fo:
    fmt = "%5.2f %10s %6.0f %6.0f" \
        " %8.2f %8.2f %9.2f %10.2f %10.2f" \
        " %8.2f %8.2f %8.2f %9.2f %9.2f"
    fo.write("%s\n" % Util.BuildHeader(fmt, "cost_slo cost_slo_label target_iops iops" \
        " r_avg r_90 r_99 r_99.9 r_99.99" \
        " w_avg w_90 w_99 w_99.9 w_99.99"
        ))
    for cost_slo, v in sorted(costslo_tio_ylr.iteritems()):
      last_tio = sorted(v.keys())[-1]
      for tio, ylr in sorted(v.iteritems()):
        cost_slo_label = ("\"%s $%s\"" % ("R" if cost_slo in [cost_localssd, cost_ebsst1] else "M", ("%f" % cost_slo).rstrip("0").rstrip("."))) \
            if tio == last_tio \
            else "\"\""

        fo.write((fmt + "\n") % (
          cost_slo
          , cost_slo_label
          , tio
          , ylr.db_iops_stat.avg
          , ylr.r_avg
          , ylr.r_90
          , ylr.r_99
          , ylr.r_999
          , ylr.r_9999
          , ylr.w_avg
          , ylr.w_90
          , ylr.w_99
          , ylr.w_999
          , ylr.w_9999
          ))
      fo.write("\n")
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


class YcsbLogReader:
  def __init__(self, fn_in, time_begin, time_end):
    #self.overloaded = overloaded

    # Unzip when the file is not there
    if not os.path.exists(fn_in):
      fn_zipped = "%s.bz2" % fn_in
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn_in)
      Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn_in):
      raise RuntimeError("Unexpected")
    #Cons.P(fn_in)

    mo_list = []
    line_params = None
    line_run = None
    with open(fn_in) as fo:
      for line in fo:
        #Cons.P(line)
        # 2017-10-13 20:41:01:258 2 sec: 34 operations; 34 current ops/sec; est completion in 68 days 1 hours [READ: Count=28, Max=46943, Min=33,
        # Avg=32239.54, 90=45343, 99=46943, 99.9=46943, 99.99=46943] [INSERT: Count=8, Max=9343, Min=221, Avg=4660.88, 90=8695, 99=9343, 99.9=9343,
        # 99.99=9343]
        mo = re.match(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d:\d\d\d (?P<rel_time>\d+) sec: \d+ operations; " \
            "(?P<db_iops>(\d|\.)+) current ops\/sec; .*" \
            "\[READ: Count=(?P<r_cnt>\d+), Max=(?P<r_max>\d+), Min=(?P<r_min>\d+), Avg=(?P<r_avg>(\d|\.)+)," \
            " 90=(?P<r_90>\d+), 99=(?P<r_99>\d+), 99.9=(?P<r_999>\d+), 99.99=(?P<r_9999>\d+)\] " \
            "\[INSERT: Count=(?P<w_cnt>\d+), Max=(?P<w_max>\d+), Min=(?P<w_min>\d+), Avg=(?P<w_avg>(\d|\.)+)," \
            " 90=(?P<w_90>\d+), 99=(?P<w_99>\d+), 99.9=(?P<w_999>\d+), 99.99=(?P<w_9999>\d+)\] " \
            , line)
        if mo is None:
          continue

        total_seconds = int(mo.group("rel_time"))
        s = total_seconds % 60
        total_seconds -= s
        total_mins = total_seconds / 60
        m = total_mins % 60
        total_mins -= m
        h = total_mins / 60
        rel_time = "%02d:%02d:%02d" % (h, m, s)
        if (time_begin <= rel_time) and (rel_time <= time_end):
          mo_list.append((rel_time, mo))
    if len(mo_list) == 0:
      raise RuntimeError("Unexpected. Check file [%s]" % fn_in)

    cnt = 0
    db_iops = []
    r_cnt = 0
    r_avg = 0.0
    r_min = 0
    r_max = 0
    r_90  = 0
    r_99  = 0
    r_999 = 0
    r_9999 = 0
    w_cnt = 0
    w_avg = 0.0
    w_min = 0
    w_max = 0
    w_90  = 0
    w_99  = 0
    w_999 = 0
    w_9999 = 0
    for e in mo_list:
      rel_time = e[0]
      mo = e[1]
      db_iops.append(float(mo.group("db_iops")))
      r_cnt   += int(mo.group("r_cnt"))
      r_avg   += float(mo.group("r_avg"))
      r_min   += int(mo.group("r_min"))
      r_max   += int(mo.group("r_max"))
      r_90    += int(mo.group("r_90"))
      r_99    += int(mo.group("r_99"))
      r_999   += int(mo.group("r_999"))
      r_9999  += int(mo.group("r_9999"))
      w_cnt   += int(mo.group("w_cnt"))
      w_avg   += float(mo.group("w_avg"))
      w_min   += int(mo.group("w_min"))
      w_max   += int(mo.group("w_max"))
      w_90    += int(mo.group("w_90"))
      w_99    += int(mo.group("w_99"))
      w_999   += int(mo.group("w_999"))
      w_9999  += int(mo.group("w_9999"))
      cnt += 1

    self.db_iops_stat = Stat.Gen(db_iops)

    self.r_cnt  = r_cnt
    self.r_avg  = (float(r_avg ) / cnt)
    self.r_min  = (float(r_min ) / cnt)
    self.r_max  = (float(r_max ) / cnt)
    self.r_90   = (float(r_90  ) / cnt)
    self.r_99   = (float(r_99  ) / cnt)
    self.r_999  = (float(r_999 ) / cnt)
    self.r_9999 = (float(r_9999) / cnt)
    self.w_cnt  = (float(w_cnt ) / cnt)
    self.w_avg  = (float(w_avg ) / cnt)
    self.w_min  = (float(w_min ) / cnt)
    self.w_max  = (float(w_max ) / cnt)
    self.w_90   = (float(w_90  ) / cnt)
    self.w_99   = (float(w_99  ) / cnt)
    self.w_999  = (float(w_999 ) / cnt)
    self.w_9999 = (float(w_9999) / cnt)
