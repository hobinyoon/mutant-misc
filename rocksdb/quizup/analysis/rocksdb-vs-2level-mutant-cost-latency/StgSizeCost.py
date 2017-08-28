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
		fn = "%s/../storage/.result/%s/data-size-by-stg-devs-by-time" \
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
				fn = "%s/../storage/.result/%s/data-size-by-stg-devs-by-time" % (os.path.dirname(__file__), st)
				if not os.path.exists(fn):
					fo.write("%s/../storage/calc/calc.py --simulation_time_begin=%s\n" % (os.path.dirname(__file__), st))
			fo.flush()
			if os.fstat(fo.fileno()).st_size > 0:
				with Cons.MT("Calculating cost in parallel ..."):
					Util.RunSubp("parallel :::: %s" % fo.name)
	else:
		with Cons.MT("Calculating cost ..."):
			# Serial processing. Useful for debugging
			for st in list_sim_times:
				# Calculate cost only if the result file doesn't exist
				fn = "%s/../storage/.result/%s/data-size-by-stg-devs-by-time" % (os.path.dirname(__file__), st)
				if not os.path.exists(fn):
					Util.RunSubp("%s/../storage/calc/calc.py --simulation_time_begin=%s" % (os.path.dirname(__file__), st))


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


# TODO: clean up
#
## TODO: revisit
#_exp_list_mutant = None
#_exp_rocksdb_simulation_time_begin = None
#
#
#
#def GetStgSizeCostData():
#	dn = "%s/.output" % os.path.dirname(__file__)
#	Util.MkDirs(dn)
#	fn_out = "%s/2level-mutant-stg-sizetime-cost-by-sstmigtempthresholds" % dn
#	fn_out_individual = "%s-individual" % fn_out
#	if os.path.exists(fn_out) and os.path.exists(fn_out_individual):
#		return (fn_out, fn_out_individual)
#
#	global _exp_list_mutant
#	global _exp_rocksdb_simulation_time_begin
#	exp_list_root = Manifest.Get("2-level Mutant storage by SSTable migration temperature thresholds. On EC2")
#	_exp_list_mutant = exp_list_root["Mutant"]["By SSTable migration temperature thresholds"]
#
#	# Just checking the list
#	if False:
#		for sst_mig_temp_threshold, exps in _exp_list_mutant.iteritems():
#			for simulation_time_begin in exps:
#				Cons.P("Mutant: %f %s" % (float(sst_mig_temp_threshold), simulation_time_begin))
#
#	_exp_rocksdb_simulation_time_begin = exp_list_root["UnmodifiedRocksDB"]
#	#Cons.P("UnmodifiedRocksDB: %s" % _exp_rocksdb_simulation_time_begin)
#
#	# Get stg stat by parsing the tail part of the generated file
#	# {sst_mig_temp_threshold: SizetimeCostByStgdev}
#	mutant_migth_stg_stat = {}
#	rocksdb_stg_stat = None
#
#	with Cons.MT("Parsing logs ..."):
#		# TODO: pass the list of all simulation_time_begin. Fix when needed
#		_CalcCost()
#
#		for sst_mig_temp_threshold, exps in _exp_list_mutant.iteritems():
#			for simulation_time_begin in exps:
#				sst_mig_temp_threshold = float(sst_mig_temp_threshold)
#				#Cons.P("sst_mig_temp_threshold=%6.2f" % sst_mig_temp_threshold)
#				if sst_mig_temp_threshold != _GetSstMigTempThreshold(simulation_time_begin):
#					raise RuntimeError("Unexpected [%s] != [%s]" % (sst_mig_temp_threshold, _GetSstMigTempThreshold(simulation_time_begin)))
#				if sst_mig_temp_threshold not in mutant_migth_stg_stat:
#					mutant_migth_stg_stat[sst_mig_temp_threshold] = StatSizetimeCostByStgdev()
#				mutant_migth_stg_stat[sst_mig_temp_threshold].Add(_GetSizetimeCostByStgdev(simulation_time_begin))
#		#Cons.P(pprint.pformat(mutant_migth_stg_stat))
#		rocksdb_stg_stat = _GetSizetimeCostByStgdev(_exp_rocksdb_simulation_time_begin)
#
#	with open(fn_out_individual, "w") as fo:
#		fmt = "%15s %17s %8.6f %8.6f %8.6f %8.6f %8.6f" \
#				" %8.6f %8.6f %8.6f %8.6f %8.6f"
#		fo.write("%s\n" % Util.BuildHeader(fmt,
#			"sst_migration_temperature_threshold" \
#			" simulation_begin_time" \
#			" size_time_local_ssd" \
#			" size_time_ebs_ssd" \
#			" size_time_ebs_mag" \
#			" size_time_ebs_mag_cold" \
#			" size_time_sum" \
#			" cost_local_ssd" \
#			" cost_ebs_ssd" \
#			" cost_ebs_mag" \
#			" cost_ebs_mag_cold" \
#			" cost_sum" \
#			))
#		for migth, stat in sorted(mutant_migth_stg_stat.iteritems()):
#			for e in stat.Exps():
#				fo.write((fmt + "\n") % (migth
#					, e.SimulationTimeBegin()
#					, e.SizeTime("Local SSD")
#					, e.SizeTime("EBS SSD")
#					, e.SizeTime("EBS Mag")
#					, e.SizeTime("EBS Mag Cold")
#					, e.SizeTime("Sum")
#					, e.Cost("Local SSD")
#					, e.Cost("EBS SSD")
#					, e.Cost("EBS Mag")
#					, e.Cost("EBS Mag Cold")
#					, e.Cost("Sum")
#					))
#		fo.write("#" + (("%s\n" % fmt) % ("RocksDB"
#			, rocksdb_stg_stat.SimulationTimeBegin()
#			, rocksdb_stg_stat.SizeTime("Local SSD")
#			, rocksdb_stg_stat.SizeTime("EBS SSD")
#			, rocksdb_stg_stat.SizeTime("EBS Mag")
#			, rocksdb_stg_stat.SizeTime("EBS Mag Cold")
#			, rocksdb_stg_stat.SizeTime("Sum")
#			, rocksdb_stg_stat.Cost("Local SSD")
#			, rocksdb_stg_stat.Cost("EBS SSD")
#			, rocksdb_stg_stat.Cost("EBS Mag")
#			, rocksdb_stg_stat.Cost("EBS Mag Cold")
#			, rocksdb_stg_stat.Cost("Sum")
#			))[1:])
#	Cons.P("Created %s %d" % (fn_out_individual, os.path.getsize(fn_out_individual)))
#
#	with open(fn_out, "w") as fo:
#		fmt = "%15s" \
#				" %8.6f %8.6f %8.6f %8.6f %8.6f" \
#				" %8.6f %8.6f %8.6f %8.6f %8.6f"
#		fo.write("%s\n" % Util.BuildHeader(fmt,
#			"sst_migration_temperature_threshold" \
#			" size_time_local_ssd" \
#			" size_time_ebs_ssd" \
#			" size_time_ebs_mag" \
#			" size_time_ebs_mag_cold" \
#			" size_time_sum" \
#			" cost_local_ssd" \
#			" cost_ebs_ssd" \
#			" cost_ebs_mag" \
#			" cost_ebs_mag_cold" \
#			" cost_sum" \
#			))
#		for migth, stat in sorted(mutant_migth_stg_stat.iteritems()):
#			fo.write((fmt + "\n") % (migth
#				, stat.SizeTime("Local SSD")[0]
#				, stat.SizeTime("EBS SSD")[0]
#				, stat.SizeTime("EBS Mag")[0]
#				, stat.SizeTime("EBS Mag Cold")[0]
#				, stat.SizeTime("Sum")[0]
#				, stat.Cost("Local SSD")[0]
#				, stat.Cost("EBS SSD")[0]
#				, stat.Cost("EBS Mag")[0]
#				, stat.Cost("EBS Mag Cold")[0]
#				, stat.Cost("Sum")[0]
#				))
#		fo.write("#" + (("%s\n" % fmt) % ("RocksDB"
#			, rocksdb_stg_stat.SizeTime("Local SSD")
#			, rocksdb_stg_stat.SizeTime("EBS SSD")
#			, rocksdb_stg_stat.SizeTime("EBS Mag")
#			, rocksdb_stg_stat.SizeTime("EBS Mag Cold")
#			, rocksdb_stg_stat.SizeTime("Sum")
#			, rocksdb_stg_stat.Cost("Local SSD")
#			, rocksdb_stg_stat.Cost("EBS SSD")
#			, rocksdb_stg_stat.Cost("EBS Mag")
#			, rocksdb_stg_stat.Cost("EBS Mag Cold")
#			, rocksdb_stg_stat.Cost("Sum")
#			))[1:])
#	Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
#
#	return (fn_out, fn_out_individual)
#	# Strange: I expected size*time to be about the same. Could be explained by
#	# multiple records with the same key getting merged more ofen.
#	# We'll see what it's like after calculating the number of writes per record.
#
#
## Returns (ur_cost_local_ssd, ur_cost_ebs_ssd, ur_sizetime)
#def GetUnmodifiedRocksDBSizeCostData():
#	fn = "%s/.output/2level-mutant-stg-sizetime-cost-by-sstmigtempthresholds" % os.path.dirname(__file__)
#	with open(fn) as fo:
#		found_rocksdb_line = False
#		for line in fo:
#			if line.startswith("#"):
#				t = line.split()
#				if len(t) == 12 and t[1] == "RocksDB":
#					found_rocksdb_line = True
#					#Cons.P(line)
#					#       RocksDB 0.841414 0.000000 0.000000 0.000000 0.841414 0.444267 0.000000 0.000000 0.000000 0.444267
#					size_time = float(t[6])
#					cost_local_ssd = float(t[7])
#					# RocksDB on EBS SSD
#					# Per GB/Month price
#					PRICE_LOCAL_SSD = 0.528
#					PRICE_EBS_SSD = 0.100
#					cost_ebs_ssd = cost_local_ssd * PRICE_EBS_SSD / PRICE_LOCAL_SSD
#					return (cost_local_ssd, cost_ebs_ssd, size_time)
#		if not found_rocksdb_line:
#			raise RuntimeError("Unexpected")
