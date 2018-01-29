import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Stat


def Get1MinMemUsage(dn_log_job, exp_dt):
  #Cons.P("%s %s" % (dn_log_job, exp_dt))
  fn = "%s/procmon/%s" % (dn_log_job, exp_dt)
  if not os.path.exists(fn):
    fn_zipped = "%s.bz2" % fn
    if not os.path.exists(fn_zipped):
      raise RuntimeError("Unexpected: %s" % fn)
    Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
  if not os.path.exists(fn):
    raise RuntimeError("Unexpected")

  exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")

  hm_mem = {}
  with open(fn) as fo:
    for line in fo:
      t = line.strip().split()
      dt = datetime.datetime.strptime(t[0], "%y%m%d-%H%M%S")
      rss = int(t[2]) * 4096
      #Cons.P("%s %d" % (dt, rss))

      # Convert to relative time
      rel_dt = dt - exp_begin_dt
      totalSeconds = rel_dt.seconds
      hours, remainder = divmod(totalSeconds, 3600)
      minutes, seconds = divmod(remainder, 60)
      hm_str = "%02d:%02d" % (hours, minutes)

      if hm_str not in hm_mem:
        hm_mem[hm_str] = []
      hm_mem[hm_str].append(rss)

  hm_mem_stat = {}
  for hm, v in hm_mem.iteritems():
    l = len(v)
    avg = 0 if l == 0 else (float(sum(v)) / l)
    hm_mem_stat[hm] = avg
  return hm_mem_stat


def GenMemStatByHour(dn_log_job, exp_dt):
  #Cons.P("%s %s" % (dn_log_job, exp_dt))
  fn = "%s/procmon/%s" % (dn_log_job, exp_dt)
  if not os.path.exists(fn):
    fn_zipped = "%s.bz2" % fn
    if not os.path.exists(fn_zipped):
      raise RuntimeError("Unexpected: %s" % fn)
    Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
  if not os.path.exists(fn):
    raise RuntimeError("Unexpected")

  exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")

  # man proc. statm

  hour_mems = {}
  with open(fn) as fo:
    for line in fo:
      t = line.strip().split()
      dt = datetime.datetime.strptime(t[0], "%y%m%d-%H%M%S")
      rss = int(t[2]) * 4096
      #Cons.P("%s %d" % (dt, rss))

      # Convert to relative time
      rel_dt = dt - exp_begin_dt
      totalSeconds = rel_dt.seconds
      h, remainder = divmod(totalSeconds, 3600)

      if h not in hour_mems:
        hour_mems[h] = []
      hour_mems[h].append(rss)

  hour_memstat = {}
  for h, mems in sorted(hour_mems.iteritems()):
    hour_memstat[h] = Stat.Gen(mems)
  return hour_memstat


def GetFnForPlot(dn_log, job_id, exp_dt):
  fn_out = "%s/mem-%s" % (Conf.GetOutDir(), exp_dt)
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Creating memory usage file for plotting ..."):
    fn = "%s/%s/procmon/%s" % (dn_log, job_id, exp_dt)
    if not os.path.exists(fn):
      fn_zipped = "%s.bz2" % fn
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn)
      Util.RunSubp("cd %s && bzip2 -dk %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn):
      raise RuntimeError("Unexpected")

    exp_begin_dt = datetime.datetime.strptime(exp_dt, "%y%m%d-%H%M%S.%f")

    # man proc. statm
    dt_rss = {}
    with open(fn) as fo:
      for line in fo:
        t = line.strip().split()
        dt = datetime.datetime.strptime(t[0], "%y%m%d-%H%M%S")
        rss = float(t[2]) * 4096 / 1024 / 1024 / 1024
        #Cons.P("%s %d" % (dt, rss))

        # Convert to relative time
        rel_dt = dt - exp_begin_dt
        totalSeconds = rel_dt.seconds
        hours, remainder = divmod(totalSeconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        rel_dt_str = "%02d:%02d:%02d" % (hours, minutes, seconds)
        dt_rss[rel_dt_str] = rss

    with open(fn_out, "w") as fo:
      fmt = "%8s %6.2f"
      header = Util.BuildHeader(fmt, "dt rss_in_gb")
      i = 0
      for dt, rss in sorted(dt_rss.iteritems()):
        if i % 40 == 0:
          fo.write(header + "\n")
        fo.write((fmt + "\n") % (dt, rss))
        i += 1
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
    return fn_out
