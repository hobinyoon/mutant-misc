import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class SimTime:
	# Get the simulation/simulated time begin/end by parsing a client log file
	# with the the same simulation time begin
	def __init__(self, simulation_time_begin):
		with Cons.MT("Init SimTime ...", print_time=False):
			self.simulation_time_begin = None
			self.simulation_time_end = None
			self.simulated_time_begin = None
			self.simulated_time_end = None

			dn = "%s/work/mutant/misc/rocksdb/log/client" % os.path.expanduser("~")
			fn = "%s/%s" % (dn, simulation_time_begin)
			if not os.path.isfile(fn):
				fn_7z = "%s.7z" % fn
				if not os.path.isfile(fn_7z):
					raise RuntimeError("Unexpected")
				Util.RunSubp("cd %s && 7z e %s" % (dn, fn_7z))
			if not os.path.isfile(fn):
				raise RuntimeError("Unexpected")

			with open(fn) as fo:
				for line in fo:
					#Cons.P(line)
					# simulation_time_end  : 161227-162418.288
					mo = re.match(r"# simulation_time_begin: (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
					if mo is not None:
						self.simulation_time_begin = mo.group("dt")
						if self.simulation_time_begin != simulation_time_begin:
							raise RuntimeError("Unexpected")
						self.simulation_time_begin = datetime.datetime.strptime(self.simulation_time_begin, "%y%m%d-%H%M%S.%f")
						continue

					mo = re.match(r"# simulation_time_end  : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
					if mo is not None:
						self.simulation_time_end = mo.group("dt")
						self.simulation_time_end = datetime.datetime.strptime(self.simulation_time_end, "%y%m%d-%H%M%S.%f")
						continue

					mo = re.match(r"# simulated_time_begin : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
					if mo is not None:
						self.simulated_time_begin = mo.group("dt")
						self.simulated_time_begin = datetime.datetime.strptime(self.simulated_time_begin, "%y%m%d-%H%M%S.%f")
						continue

					mo = re.match(r"# simulated_time_end   : (?P<dt>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)", line)
					if mo is not None:
						self.simulated_time_end = mo.group("dt")
						self.simulated_time_end = datetime.datetime.strptime(self.simulated_time_end, "%y%m%d-%H%M%S.%f")
						# Got all you needed. break to save time
						break

			if True:
				Cons.P("simulation_time_begin: %s" % self.simulation_time_begin)
				Cons.P("simulation_time_end  : %s" % self.simulation_time_end)
				Cons.P("simulated_time_begin : %s" % self.simulated_time_begin)
				Cons.P("simulated_time_end   : %s" % self.simulated_time_end)


	# s - self.simulation_time_begin : self.simulation_time_end - self.simulation_time_begin = x - self.simulated_time_begin : self.simulated_time_end - self.simulated_time_begin
	# x - self.simulated_time_begin = (s - self.simulation_time_begin) * (self.simulated_time_end - self.simulated_time_begin) / (self.simulation_time_end - self.simulation_time_begin)
	# x = (s - self.simulation_time_begin) * (self.simulated_time_end - self.simulated_time_begin) / (self.simulation_time_end - self.simulation_time_begin) + self.simulated_time_begin
	def ToSimulatedTime(self, s):
		return datetime.timedelta(seconds = ((s - self.simulation_time_begin).total_seconds() \
				* (self.simulated_time_end - self.simulated_time_begin).total_seconds() \
				/ (self.simulation_time_end - self.simulation_time_begin).total_seconds())) \
				+ self.simulated_time_begin


	def ToSimulatedTimeDur(self, simulation_time_dur):
		return float(simulation_time_dur) \
				/ (self.simulation_time_end - self.simulation_time_begin).total_seconds() \
				* (self.simulated_time_end - self.simulated_time_begin).total_seconds()


	def SimulatedTimeBegin(self):
		return self.simulated_time_begin


	def SimulatedTimeEnd(self):
		return self.simulated_time_end


	def SimulatedTimeDur(self):
		return self.simulated_time_end - self.simulated_time_begin
