import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Stat


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
