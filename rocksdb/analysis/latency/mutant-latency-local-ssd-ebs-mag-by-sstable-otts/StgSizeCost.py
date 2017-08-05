import base64
import os
import pprint
import re
import sys
import tempfile
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


def StgSizetimeCostRocksDb():
	exp_list_root = Conf.Manifest.Get("2-level Mutant storage by SSTable migration temperature thresholds. On EC2")
	simulation_time_begin = exp_list_root["UnmodifiedRocksDB"]
	return SizetimeCostByStgdev(simulation_time_begin)


def StgSizetimeCostMutant():
	exp_list_root = Conf.Manifest.Get("2-level Mutant storage by SSTable migration temperature thresholds. On EC2")

	all_exps = []
	for sst_mig_temp_threshold, v in exp_list_root["Mutant"]["By SSTable migration temperature thresholds"].iteritems():
		for simulation_time_begin in v:
			all_exps.append(simulation_time_begin)
	_CalcCost(all_exps)

	# {sst_mig_temp_threshold: StatSizetimeCostByStgdev}
	mutant_migth_stg_stat = {}
	with Cons.MT("Calculating storage cost ..."):
		for sst_mig_temp_threshold, v in exp_list_root["Mutant"]["By SSTable migration temperature thresholds"].iteritems():
			sst_mig_temp_threshold = float(sst_mig_temp_threshold)
			for simulation_time_begin in v:
				# Validate if the log is for the correct sst_mig_temp_threshold
				if sst_mig_temp_threshold != _GetSstMigTempThreshold(simulation_time_begin):
					raise RuntimeError("Unexpected [%s] != [%s]" % (sst_mig_temp_threshold, _GetSstMigTempThreshold(simulation_time_begin)))

				if sst_mig_temp_threshold not in mutant_migth_stg_stat:
					mutant_migth_stg_stat[sst_mig_temp_threshold] = StatSizetimeCostByStgdev()
				mutant_migth_stg_stat[sst_mig_temp_threshold].Add(SizetimeCostByStgdev(simulation_time_begin))
		#Cons.P(pprint.pformat(mutant_migth_stg_stat))

	return mutant_migth_stg_stat


class SizetimeCostByStgdev:
	def __init__(self, simulation_time_begin):
		# Generate the storage file when not exists
		_CalcCost([simulation_time_begin])

		self.simulation_time_begin = simulation_time_begin
		self.dev_sizetime = {}
		self.dev_cost = {}
		self._ReadStorageAnalysisResultFile()

	def _ReadStorageAnalysisResultFile(self):
		fn = "%s/../../storage/.result/%s/data-size-by-stg-devs-by-time" \
				% (os.path.dirname(__file__), self.simulation_time_begin)
		with open(fn) as fo:
			while True:
				line = fo.readline()
				if not line:
					break
				# Data size-time (GB*Month):
				#   Local SSD   : 0.022983
				#   EBS SSD     : 0.116354
				#   EBS Mag     : 0.000000
				#   EBS Mag Cold: 0.000000
				#   Sum         : 0.139338
				# Storage cost ($):
				#   Local SSD   : 0.012135
				#   EBS SSD     : 0.011635
				#   EBS Mag     : 0.000000
				#   EBS Mag Cold: 0.000000
				#   Sum         : 0.023771
				if line == "# Data size-time (GB*Month):\n":
					for i in range(5):
						line = fo.readline()
						if not line:
							raise RuntimeError("Unexpected")
						mo = re.match(r"#   (?P<dev>(\w| )+): (?P<v>(\d|\.)+)\n", line)
						if mo is None:
							raise RuntimeError("Unexpected")
						dev = mo.group("dev").strip()
						v = float(mo.group("v"))
						#Cons.P("size-time: %s %f" % (dev, v))
						self.dev_sizetime[dev] = v

				elif line == "# Storage cost ($):\n":
					for i in range(5):
						line = fo.readline()
						if not line:
							raise RuntimeError("Unexpected")
						mo = re.match(r"#   (?P<dev>(\w| )+): (?P<v>(\d|\.)+)\n", line)
						if mo is None:
							raise RuntimeError("Unexpected")
						dev = mo.group("dev").strip()
						v = float(mo.group("v"))
						#Cons.P("cost: %s %f" % (dev, v))
						self.dev_cost[dev] = v

	def __repr__(self):
		return pprint.pformat(vars(self))
	def SizeTime(self, dev):
		return self.dev_sizetime[dev]
	def Cost(self, dev):
		return self.dev_cost[dev]
	def SimulationTimeBegin(self):
		return self.simulation_time_begin


# Aggregate stat of SizetimeCostByStgdev
class StatSizetimeCostByStgdev:
	def __init__(self):
		self.exps = []
	def Add(self, st_c_by_sd):
		self.exps.append(st_c_by_sd)
	def SizeTime(self, dev):
		sum_ = 0.0
		min_ = None
		max_ = None
		for e in self.exps:
			sum_ += e.dev_sizetime[dev]
			if min_ is None:
				min_ = e.dev_sizetime[dev]
			else:
				min_ = min(min_, e.dev_sizetime[dev])
			if max_ is None:
				max_ = e.dev_sizetime[dev]
			else:
				max_ = max(max_, e.dev_sizetime[dev])
		avg = sum_ / float(len(self.exps))
		return (avg, min_, max_)
	def Cost(self, dev):
		sum_ = 0.0
		min_ = None
		max_ = None
		for e in self.exps:
			sum_ += e.dev_cost[dev]
			if min_ is None:
				min_ = e.dev_cost[dev]
			else:
				min_ = min(min_, e.dev_cost[dev])
			if max_ is None:
				max_ = e.dev_cost[dev]
			else:
				max_ = max(max_, e.dev_cost[dev])
		avg = sum_ / float(len(self.exps))
		return (avg, min_, max_)
	def __repr__(self):
		return pprint.pformat(vars(self))
	def Exps(self):
		return self.exps


def _CalcCost(list_sim_times):
	if True:
		# Parallel processing. Super fast.
		with tempfile.NamedTemporaryFile() as fo:
			for st in list_sim_times:
				# Calculate cost only if the result file doesn't exist
				fn = "%s/../../storage/.result/%s/data-size-by-stg-devs-by-time" % (os.path.dirname(__file__), st)
				if not os.path.exists(fn):
					fo.write("%s/../../storage/calc/calc.py --simulation_time_begin=%s\n" % (os.path.dirname(__file__), st))
			fo.flush()
			if os.fstat(fo.fileno()).st_size > 0:
				with Cons.MT("Calculating cost in parallel ..."):
					Util.RunSubp("parallel :::: %s" % fo.name)
	else:
		with Cons.MT("Calculating cost ..."):
			# Serial processing. Useful for debugging
			for st in list_sim_times:
				# Calculate cost only if the result file doesn't exist
				fn = "%s/../../storage/.result/%s/data-size-by-stg-devs-by-time" % (os.path.dirname(__file__), st)
				if not os.path.exists(fn):
					Util.RunSubp("%s/../../storage/calc/calc.py --simulation_time_begin=%s" % (os.path.dirname(__file__), st))


def _GetSstMigTempThreshold(simulation_time_begin):
	fn_client_log = "%s/work/mutant/misc/rocksdb/log/client/%s" % (os.path.expanduser("~"), simulation_time_begin)

	# Gather all options. Might be useful in the future.
	quizup_options = {}

	with open(fn_client_log) as fo:
		for line in fo:
			# # Quizup run script options: <Values at 0x7f85c8de37e8:
			# {'memory_limit_in_mb': 0, 'simulation_time_dur_in_sec': '2000',
			# 'workload_stop_at': '-1.0', 'slow_dev2_path': None,
			# 'evict_cached_data': 'true', 'fast_dev_path':
			# '/mnt/local-ssd1/rocksdb-data', 'upload_result_to_s3': True,
			# 'mutant_enabled': 'true', 'init_db_to_90p_loaded': 'false',
			# 'slow_dev1_path': '/mnt/ebs-gp2/rocksdb-data-quizup-t1',
			# 'workload_start_from': '-1.0', 'slow_dev3_path': None, 'db_path':
			# '/mnt/local-ssd1/rocksdb-data/quizup'}>
			#
			# Without =, it gets stuck when the input string contains =. Interesting.
			mo = re.match(r"# Quizup run script options: <Values at 0x(\d|\w)+: " \
					"(?P<options>{('|\w|:| |\d|,|-|\.|/|=)+})" \
					">" \
					, line)
			if mo is not None:
				options = mo.group("options")
				#Cons.P("options=[%s]" % options)
				for k in ["exp_desc"
						, "memory_limit_in_mb"
						, "fast_dev_path"
						, "slow_dev1_path"
						, "slow_dev2_path"
						, "slow_dev3_path"
						, "db_path"
						, "init_db_to_90p_loaded"
						, "evict_cached_data"
						, "upload_result_to_s3"

						, "mutant_enabled"
						, "workload_start_from"
						, "workload_stop_at"
						, "simulation_time_dur_in_sec"
						, "sst_migration_temperature_threshold"
						]:
					mo1 = re.match(".*" \
							"'%s': '?(?P<%s>(\w|\d|=|/|\.|-)+)'?" \
							".*" \
							% (k, k)
							, options)
					if mo1 is None:
						quizup_options[k] = None
					else:
						if k == "exp_desc":
							quizup_options[k] = base64.b64decode(mo1.group(k))
						else:
							quizup_options[k] = mo1.group(k)
					#Cons.P("  %s: %s" % (k, quizup_options[k]))
	return float(quizup_options["sst_migration_temperature_threshold"])
