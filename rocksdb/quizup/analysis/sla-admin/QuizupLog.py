import os
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

class QuizupLog:
  def __init__(self, fn):
    # simulated/simulation time 0-3
    self.simtime = {}

    if not os.path.exists(fn):
      fn_zipped = "%s.7z" % fn
      if not os.path.exists(fn_zipped):
        raise RuntimeError("Unexpected: %s" % fn)
      Util.RunSubp("cd %s && 7z e %s > /dev/null" % (os.path.dirname(fn_zipped), os.path.basename(fn_zipped)))
    if not os.path.exists(fn):
      raise RuntimeError("Unexpected")

    self.fn = fn

    with open(fn) as fo:
      #where = "before_body"
      for line in fo:
        line = line.strip()
        if line.startswith("# sst_ott: "):
          mo = re.match(r"# sst_ott: (?P<v>(\d|\.)+)", line)
          if mo is None:
            raise RuntimeError("Unexpected")
          self.sst_ott = float(mo.group("v"))
          #Cons.P(self.sst_ott)
          continue
          # # simulation_time_0: 170828-215755.938
        if line.startswith("# simulat"):
          mo = re.match(r"# (?P<k>simulat\w+_time_\d): +(?P<v>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
          if mo is None:
            continue
          self.simtime[mo.group("k")] = mo.group("v")
          continue
        # No need to parse the body. You can plot it directly.
        ## Detect the beginning of the stat
        #if where == "before_body":
        #  # #          1      2                 3                 4      5       6      7       8       9        10
        #  mo = re.match(r"# +1 +2 +3 +4 +5 +6 +7 +8 +9.+", line)
        #  #Cons.P(mo)
        #  if mo is not None:
        #    where = "in_body"
        #  continue
        #elif where == "in_body":
        #  # # 7153287 / 707523953 operations requested. 6025758 puts, 1127529 gets.
        #  mo = re.match(r"#.+operations requested.+", line)
        #  if mo is not None:
        #    where = "after_body"
        #    continue
        #  # Parse in-body
        #  t = re.split(" +", line)
        #  simulation_time_rel = t[0]
        #  simulation_time = t[2]
        #  reads = int(t[28])
        #  r_lat_us = int(t[29])
        #  Cons.P(line)
        #elif where == "after_body":
        #  # You can parse Quizup run script options. Let's see if needed
        #  pass

  def SimTime(self, type):
    return self.simtime[type]
