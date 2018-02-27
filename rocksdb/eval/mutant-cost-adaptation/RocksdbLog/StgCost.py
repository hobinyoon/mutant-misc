import datetime
import json
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class StgCost:
  def __init__(self, exp_dt):
    self.exp_dt = exp_dt
    self.stg_pricing = None
    self.target_cost = None
    # {relative_time: target_cost}
    self.cost_changes = {}
    self.migration_resistance = None


  def SetStgPricing(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_list: (?P<v0>(\d|\.)+) (?P<v1>(\d|\.)+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    self.stg_pricing = [float(mo.group("v0")), float(mo.group("v1"))]


  # 2018/01/23-22:53:48.875128 7f3300cd8700   stg_cost_slo: 0.300000
  def SetTargetCost(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_slo: (?P<v>(\d|\.)+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    self.target_cost = float(mo.group("v"))
    self.cost_changes[datetime.timedelta()] = self.target_cost


  def SetMigrationResistance(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .*   stg_cost_slo_epsilon: (?P<v>(\d|\.)+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    self.migration_resistance = float(mo.group("v"))


  def SetCostChange(self, line):
    mo = re.match(r"(?P<ts>(\d|\/|-|:|\.)+) .+EVENT_LOG_v1 (?P<json>.+)", line)
    if mo is None:
      raise RuntimeError("Unexpected: [%s]" % line)
    j1 = json.loads(mo.group("json"))
    ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
    ts_rel = ts - datetime.datetime.strptime(self.exp_dt, "%y%m%d-%H%M%S.%f")
    cost = float(j1["Set target_cost to "])
    #Cons.P("%s %s" % (ts, cost))
    self.cost_changes[ts_rel] = cost


  def AddStatToFile(self, fn):
    with Cons.MT("Adding storage cost to the SSTable stat file ..."):
      fn2 = "%s.tmp" % fn

      with open(fn2, "w") as fo2:
        fo2.write("# Storage cost info:\n")
        fo2.write("#   stg_pricing=[%s]\n" % ", ".join(str(i) for i in self.stg_pricing))
        fo2.write("#   target_cost=%f\n" % self.target_cost)
        fo2.write("#   migration_resistance=%f\n" % self.migration_resistance)
        fo2.write("#   cost_changes=[%s]\n" % ", ".join("%s %f" % (k, v) for k, v in sorted(self.cost_changes.iteritems())))
        fo2.write("\n")
        with open(fn) as fo:
          for line in fo:
            fo2.write(line)

      os.rename(fn2, fn)
      Cons.P("Updated %s %d" % (fn, os.path.getsize(fn)))


  def __repr__(self):
    s = []
    for k, v in sorted(vars(self).items()):
      s.append("%s=%s" % (k, v))
    return "<%s>" % " ".join(s)
