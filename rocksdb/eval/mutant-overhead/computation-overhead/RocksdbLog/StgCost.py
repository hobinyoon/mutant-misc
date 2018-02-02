import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class StgCost:
  def __init__(self, rocks_log_reader):
    self.rocks_log_reader = rocks_log_reader
    self._Calc()

  def _Calc(self):
    se = self.rocks_log_reader.sst_events
    time_max = datetime.timedelta(seconds=8*3600)
    self.stg_time_size = se.GetStgTimeSize(time_max)

    stg_pricing = self.rocks_log_reader.stg_pricing
    self.fast_stg_cost = self.stg_time_size[0] * stg_pricing[0]
    self.slow_stg_cost = self.stg_time_size[1] * stg_pricing[1]
    self.stg_cost = self.fast_stg_cost + self.slow_stg_cost

    self.stg_unit_cost = self.stg_cost / sum(self.stg_time_size)

    #Cons.P("stg_pricing=[%s]" % ", ".join(str(i) for i in stg_pricing))
    #Cons.P("stg_cost_slo=%f" % lr.stg_cost_slo)
    #Cons.P("stg_cost_slo_epsilon=%f" % lr.stg_cost_slo_epsilon)

    #Cons.P("fast_stg_time_size_gb_month=%f" % self.stg_time_size[0])
    #Cons.P("fast_stg_cost=%f" % self.fast_stg_cost)
    #Cons.P("slow_stg_time_size_gb_month=%f" % self.stg_time_size[1])
    #Cons.P("slow_stg_cost=%f" % self.slow_stg_cost)
    #Cons.P("total_stg_cost=%f" % self.stg_cost)

  def __repr__(self):
    s = []
    for k, v in sorted(vars(self).items()):
      if k == "rocks_log_reader":
        continue
      s.append("%s=%s" % (k, v))
    return "<%s>" % " ".join(s)

  def AddStatToFile(self, fn):
    with Cons.MT("Adding storage cost to the SSTable stat file ..."):
      stg_pricing = self.rocks_log_reader.stg_pricing
      lr = self.rocks_log_reader

      fn2 = "%s.tmp" % fn

      with open(fn2, "w") as fo2:
        fo2.write("# Storage cost:\n")
        fo2.write("#   stg_pricing=[%s]\n" % ", ".join(str(i) for i in stg_pricing))
        fo2.write("#   stg_cost_slo=%f\n" % lr.stg_cost_slo)
        fo2.write("#   stg_cost_slo_epsilon=%f\n" % lr.stg_cost_slo_epsilon)
        fo2.write("#   fast_stg_time_size_gb_month=%f\n" % self.stg_time_size[0])
        fo2.write("#   fast_stg_cost=%f\n" % self.fast_stg_cost)
        fo2.write("#   slow_stg_time_size_gb_month=%f\n" % self.stg_time_size[1])
        fo2.write("#   slow_stg_cost=%f\n" % self.slow_stg_cost)
        fo2.write("#   total_stg_cost=%f\n" % self.stg_cost)
        fo2.write("#   total_stg_unit_cost=%f\n" % self.stg_unit_cost)
        fo2.write("\n")
        with open(fn) as fo:
          for line in fo:
            fo2.write(line)

      os.rename(fn2, fn)
      Cons.P("Updated %s %d" % (fn, os.path.getsize(fn)))
