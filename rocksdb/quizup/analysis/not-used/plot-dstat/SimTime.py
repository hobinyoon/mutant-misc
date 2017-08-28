import datetime
import re

import Cons
import Conf



_simulation_time_begin = None
_simulation_time_end = None
_simulated_time_begin = None
_simulated_time_end = None


# Get the simulation/simulated time begin/end by parsing a client log file with
# the the same simulation time begin
def Init():
	with Cons.MT("Init Conf ...", print_time=False):
		global _simulation_time_begin
		global _simulation_time_end
		global _simulated_time_begin
		global _simulated_time_end

		fn = "%s/client/%s" % (Conf.GetDir("log_dir"), Conf.Get("simulation_time_begin"))
		with open(fn) as fo:
			for line in fo:
				#Cons.P(line)
				# simulation_time_end  : 161227-162418.288
				mo = re.match(r"# simulation_time_begin: (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
				if mo is not None:
					_simulation_time_begin = mo.group("dt")
					if _simulation_time_begin != Conf.Get("simulation_time_begin"):
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
					continue

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
