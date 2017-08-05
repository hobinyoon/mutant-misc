import base64
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class ClientLogReader:
	def __init__(self, simulation_time_begin):
		self.simulation_time_begin = simulation_time_begin
		self.mutant_enabled = None
		self.options = {}
		self.Read()
	
	def Read(self):
		dn = "%s/work/mutant/misc/rocksdb/log/client" % os.path.expanduser("~")
		fn = "%s/%s" % (dn, self.simulation_time_begin)

		if not os.path.exists(fn):
			fn_7z = "%s/%s.7z" % (dn, self.simulation_time_begin)
			if not os.path.exists(fn_7z):
				raise RuntimeError("Unexpected")
			Util.RunSubp("cd %s && 7z e %s.7z" % (dn, self.simulation_time_begin))

		with open(fn) as fo:
			for line in fo:
				if len(line) == 0:
					continue
				# # Quizup run script options: <Values at 0x7f85c8de37e8:
				# {'simulation_time_dur_in_sec': '20000', 'db_path':
				# '/mnt/local-ssd1/rocksdb-data/quizup',
				# 'cache_filter_index_at_all_levels': 'true', 'workload_stop_at':
				# '-1.0', 'slow_dev2_path': None, 'evict_cached_data': 'true',
				# 'fast_dev_path': '/mnt/local-ssd1/rocksdb-data',
				# 'upload_result_to_s3': True, 'monitor_temp': 'true', 'exp_desc':
				# 'TXV0YW50IGxhdGVuY3kgYnkgY29sZCBzdG9yZ2UgZGV2aWNlcyBieSBTU1RhYmxlIG1pZ3JhdGlvbiB0ZW1wZXJhdHVyZSB0aHJlc2hvbGRz',
				# 'init_db_to_90p_loaded': 'false', 'slow_dev1_path':
				# '/mnt/ebs-gp2/rocksdb-data-quizup-t1', 'workload_start_from': '-1.0',
				# 'migrate_sstables': 'true', 'sst_migration_temperature_threshold':
				# '0.0009765625', 'slow_dev3_path': None, 'memory_limit_in_mb':
				# '9216.0'}>
				#
				# Without =, it gets stuck when the input string contains =. Interesting.
				mo = re.match(r"# Quizup run script options: <Values at 0x(\d|\w)+: " \
						"(?P<options>{('|\w|:| |\d|,|-|\.|/|=)+})" \
						">" \
						, line)
				if mo is not None:
					options = mo.group("options")
					#Cons.P("options=[%s]" % options)

					for opt in [ \
							"fast_dev_path" \
							, "slow_dev1_path" \
							, "slow_dev2_path" \
							, "slow_dev3_path" \
							, "init_db_to_90p_loaded" \
							, "memory_limit_in_mb" \
							\
							, "exp_desc" \
							, "mutant_enabled" \
							, "cache_filter_index_at_all_levels" \
							, "monitor_temp" \
							, "migrate_sstables" \
							, "workload_start_from" \
							, "workload_stop_at" \
							, "simulation_time_dur_in_sec" \
							, "sst_migration_temperature_threshold" \
							]:
						#Cons.P("%s" % opt)
						mo1 = re.match(r".+" \
								"'%s': '?(?P<%s>(\w|\d|=|-|\.|/)+)'?" \
								".*" % (opt, opt) \
								, options)
						if mo1 is not None:
							#Cons.P("%s: %s" % (opt, mo1.group(opt)))
							if opt == "exp_desc":
								self.options[opt] = base64.b64decode(mo1.group(opt))
							elif opt == "fast_dev_path":
								self.options[opt] = mo1.group(opt).split("/")[2]
							elif opt == "slow_dev1_path":
								t = mo1.group(opt).split("/")
								if len(t) > 2:
									self.options[opt] = t[2]
								else:
									self.options[opt] = None
							else:
								self.options[opt] = mo1.group(opt)
