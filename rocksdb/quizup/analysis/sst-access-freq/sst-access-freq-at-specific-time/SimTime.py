import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


_simulation_time_begin = None
_simulation_time_end = None
_simulated_time_begin = None
_simulated_time_end = None


# Get the simulation/simulated time begin/end by parsing a client log file with
# the the same simulation time begin
def Init(simulation_time_begin):
  with Cons.MT("Init Conf ...", print_time=False):
    global _simulation_time_begin
    global _simulation_time_end
    global _simulated_time_begin
    global _simulated_time_end
    _simulation_time_begin = None
    _simulation_time_end = None
    _simulated_time_begin = None
    _simulated_time_end = None

    dn = "%s/client" % Conf.GetDir("log_dir")
    fn = "%s/%s" % (dn, simulation_time_begin)
    if not os.path.isfile(fn):
      fn_7z = "%s.7z" % fn
      if not os.path.isfile(fn_7z):
        raise RuntimeError("File not found: %s" % fn_7z)
      Util.RunSubp("cd %s && 7z e %s" % (dn, fn_7z))
    if not os.path.isfile(fn):
      raise RuntimeError("Unexpected")

    with Cons.MT("Parsing simulated/simulation time from %s ..." % fn, print_time=False):
      with open(fn) as fo:
        for line in fo:
          #Cons.P(line)
          # simulation_time_end  : 161227-162418.288
          mo = re.match(r"# simulation_time_begin: (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
          if mo is not None:
            _simulation_time_begin = mo.group("dt")
            if _simulation_time_begin != simulation_time_begin:
              raise RuntimeError("Unexpected")
            _simulation_time_begin = datetime.datetime.strptime(_simulation_time_begin, "%y%m%d-%H%M%S.%f")
            continue

          mo = re.match(r"# simulation_time_end  : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
          if mo is not None:
            _simulation_time_end = mo.group("dt")
            _simulation_time_end = datetime.datetime.strptime(_simulation_time_end, "%y%m%d-%H%M%S.%f")
            continue

          mo = re.match(r"# simulated_time_begin : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
          if mo is not None:
            _simulated_time_begin = mo.group("dt")
            _simulated_time_begin = datetime.datetime.strptime(_simulated_time_begin, "%y%m%d-%H%M%S.%f")
            continue

          mo = re.match(r"# simulated_time_end   : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
          if mo is not None:
            _simulated_time_end = mo.group("dt")
            _simulated_time_end = datetime.datetime.strptime(_simulated_time_end, "%y%m%d-%H%M%S.%f")
            # Got all you needed. break to save time
            break

      Cons.P("simulation_time_begin: %s" % _simulation_time_begin)
      Cons.P("simulation_time_end  : %s" % _simulation_time_end)
      Cons.P("simulated_time_begin : %s" % _simulated_time_begin)
      Cons.P("simulated_time_end   : %s" % _simulated_time_end)


# s - _simulation_time_begin : _simulation_time_end - _simulation_time_begin = x - _simulated_time_begin : _simulated_time_end - _simulated_time_begin
# x - _simulated_time_begin = (s - _simulation_time_begin) * (_simulated_time_end - _simulated_time_begin) / (_simulation_time_end - _simulation_time_begin)
# x = (s - _simulation_time_begin) * (_simulated_time_end - _simulated_time_begin) / (_simulation_time_end - _simulation_time_begin) + _simulated_time_begin
def ToSimulatedTime(s):
  return datetime.timedelta(seconds = ((s - _simulation_time_begin).total_seconds() \
      * (_simulated_time_end - _simulated_time_begin).total_seconds() \
      / (_simulation_time_end - _simulation_time_begin).total_seconds())) \
      + _simulated_time_begin


def ToSimulatedTimeDur(simulation_time_dur):
  return float(simulation_time_dur) \
      / (_simulation_time_end - _simulation_time_begin).total_seconds() \
      * (_simulated_time_end - _simulated_time_begin).total_seconds()


def SimulatedTimeAt(p):
  return _simulated_time_begin + \
      datetime.timedelta(seconds = p * (_simulated_time_end - _simulated_time_begin).total_seconds())
