import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


_simulated_time_begin = None
_simulated_time_end = None
_simulation_time_begin = None
_simulation_time_end = None


# Get the simulation/simulated time begin/end by parsing a client log file with
# the the same simulation time begin
def Init(simulated_time_begin, simulated_time_end, simulation_time_begin, simulation_time_end):
  with Cons.MT("Init simulated/simulation time ...", print_time=False):
    global _simulated_time_begin
    global _simulated_time_end
    global _simulation_time_begin
    global _simulation_time_end

    _simulated_time_begin  = datetime.datetime.strptime(simulated_time_begin , "%y%m%d-%H%M%S.%f")
    _simulated_time_end    = datetime.datetime.strptime(simulated_time_end   , "%y%m%d-%H%M%S.%f")
    _simulation_time_begin = datetime.datetime.strptime(simulation_time_begin, "%y%m%d-%H%M%S.%f")
    _simulation_time_end   = datetime.datetime.strptime(simulation_time_end  , "%y%m%d-%H%M%S.%f")

    Cons.P("simulated_time_begin : %s" % _simulated_time_begin)
    Cons.P("simulated_time_end   : %s" % _simulated_time_end)
    Cons.P("simulation_time_begin: %s" % _simulation_time_begin)
    Cons.P("simulation_time_end  : %s" % _simulation_time_end)


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


def SimulationTimeBegin():
	return _simulation_time_begin


def ToSimulationTimeRelative(s):
  return s - _simulation_time_begin
