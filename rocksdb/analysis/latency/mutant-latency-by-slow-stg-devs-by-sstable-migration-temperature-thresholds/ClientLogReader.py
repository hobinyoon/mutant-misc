import base64
import os
import re
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


class ClientLogReader:
	def __init__(self, simulation_time_begin):
		self.simulation_time_begin = simulation_time_begin
		self.options = {}
		self.latency_rows = []
		self.system_overloaded = None
		self._Read()
		if self.options["mutant_enabled"] != "true":
			raise RuntimeError("Unexpected")
		self._CalcLatency()
	
	def _Read(self):
		dn = "%s/work/mutant/misc/rocksdb/log/client" % os.path.expanduser("~")
		fn = "%s/%s" % (dn, self.simulation_time_begin)

		if not os.path.exists(fn):
			fn_7z = "%s/%s.7z" % (dn, self.simulation_time_begin)
			if not os.path.exists(fn_7z):
				raise RuntimeError("Unexpected")
			Util.RunSubp("cd %s && 7z e %s.7z" % (dn, self.simulation_time_begin))

		#Cons.P("%s:" % self.simulation_time_begin)
		with open(fn) as fo:
			for line in fo:
				if len(line) == 0:
					continue
				if line.startswith("#"):
					self._ParseOptions(line)
				else:
					last_line = line
					self._ParseLatency(line)
		# Check if the system was overloaded
		if len(self.latency_rows) == 0:
			raise RuntimeError("Unexpected")
		simulation_time_dur = self.latency_rows[-1][0]
		# Simulation time duration
		# Normal value:                01:40:59.010
		# Detect anything bigger than: 01:41:10.000
		self.system_overloaded = ("01:41:10.000" < simulation_time_dur)
		Cons.P("Parsed %s, %5d latency_rows. simulation_time_dur=%s %s" \
				% (self.simulation_time_begin, len(self.latency_rows), simulation_time_dur
					, ("overloaded" if self.system_overloaded else "")))
	
	def _ParseOptions(self, line):
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
					self.options[k] = None
				else:
					if k == "exp_desc":
						self.options[k] = base64.b64decode(mo1.group(k))
					else:
						self.options[k] = mo1.group(k)
				#Cons.P("  %s: %s" % (k, self.options[k]))

	def _ParseLatency(self, line):
		# Get latencies
		tokens = line.split()
		if len(tokens) != 49:
			raise RuntimeError("Unexpected")
		simulated_time = tokens[3]
		simulated_time_min_latency_calc = "160727-000000.000"
		if simulated_time < simulated_time_min_latency_calc:
			return
		self.latency_rows.append(tokens)
		
	def _CalcLatency(self):
		puts     = []
		put_avg  = []
		put_99   = []
		put_991  = []
		put_992  = []
		put_993  = []
		put_994  = []
		put_995  = []
		put_996  = []
		put_997  = []
		put_998  = []
		put_999  = []
		put_9991 = []
		put_9992 = []
		put_9993 = []
		put_9994 = []
		put_9995 = []
		put_9996 = []
		put_9997 = []
		put_9998 = []
		put_9999 = []

		gets     = []
		get_avg  = []
		get_99   = []
		get_991  = []
		get_992  = []
		get_993  = []
		get_994  = []
		get_995  = []
		get_996  = []
		get_997  = []
		get_998  = []
		get_999  = []
		get_9991 = []
		get_9992 = []
		get_9993 = []
		get_9994 = []
		get_9995 = []
		get_9996 = []
		get_9997 = []
		get_9998 = []
		get_9999 = []

		for r in self.latency_rows:
			base = 7
			puts    .append(float(r[base +  0]))
			put_avg .append(float(r[base +  1]))
			put_99  .append(float(r[base +  2]))
			put_991 .append(float(r[base +  3]))
			put_992 .append(float(r[base +  4]))
			put_993 .append(float(r[base +  5]))
			put_994 .append(float(r[base +  6]))
			put_995 .append(float(r[base +  7]))
			put_996 .append(float(r[base +  8]))
			put_997 .append(float(r[base +  9]))
			put_998 .append(float(r[base + 10]))
			put_999 .append(float(r[base + 11]))
			put_9991.append(float(r[base + 12]))
			put_9992.append(float(r[base + 13]))
			put_9993.append(float(r[base + 14]))
			put_9994.append(float(r[base + 15]))
			put_9995.append(float(r[base + 16]))
			put_9996.append(float(r[base + 17]))
			put_9997.append(float(r[base + 18]))
			put_9998.append(float(r[base + 19]))
			put_9999.append(float(r[base + 20]))
			base = 28
			gets    .append(float(r[base +  0]))
			get_avg .append(float(r[base +  1]))
			get_99  .append(float(r[base +  2]))
			get_991 .append(float(r[base +  3]))
			get_992 .append(float(r[base +  4]))
			get_993 .append(float(r[base +  5]))
			get_994 .append(float(r[base +  6]))
			get_995 .append(float(r[base +  7]))
			get_996 .append(float(r[base +  8]))
			get_997 .append(float(r[base +  9]))
			get_998 .append(float(r[base + 10]))
			get_999 .append(float(r[base + 11]))
			get_9991.append(float(r[base + 12]))
			get_9992.append(float(r[base + 13]))
			get_9993.append(float(r[base + 14]))
			get_9994.append(float(r[base + 15]))
			get_9995.append(float(r[base + 16]))
			get_9996.append(float(r[base + 17]))
			get_9997.append(float(r[base + 18]))
			get_9998.append(float(r[base + 19]))
			get_9999.append(float(r[base + 20]))

		self.puts     = sum(puts    )/float(len(puts    ))
		self.put_avg  = sum(put_avg )/float(len(put_avg ))
		self.put_99   = sum(put_99  )/float(len(put_99  ))
		self.put_991  = sum(put_991 )/float(len(put_991 ))
		self.put_992  = sum(put_992 )/float(len(put_992 ))
		self.put_993  = sum(put_993 )/float(len(put_993 ))
		self.put_994  = sum(put_994 )/float(len(put_994 ))
		self.put_995  = sum(put_995 )/float(len(put_995 ))
		self.put_996  = sum(put_996 )/float(len(put_996 ))
		self.put_997  = sum(put_997 )/float(len(put_997 ))
		self.put_998  = sum(put_998 )/float(len(put_998 ))
		self.put_999  = sum(put_999 )/float(len(put_999 ))
		self.put_9991 = sum(put_9991)/float(len(put_9991))
		self.put_9992 = sum(put_9992)/float(len(put_9992))
		self.put_9993 = sum(put_9993)/float(len(put_9993))
		self.put_9994 = sum(put_9994)/float(len(put_9994))
		self.put_9995 = sum(put_9995)/float(len(put_9995))
		self.put_9996 = sum(put_9996)/float(len(put_9996))
		self.put_9997 = sum(put_9997)/float(len(put_9997))
		self.put_9998 = sum(put_9998)/float(len(put_9998))
		self.put_9999 = sum(put_9999)/float(len(put_9999))

		self.gets     = sum(gets    )/float(len(gets    ))
		self.get_avg  = sum(get_avg )/float(len(get_avg ))
		self.get_99   = sum(get_99  )/float(len(get_99  ))
		self.get_991  = sum(get_991 )/float(len(get_991 ))
		self.get_992  = sum(get_992 )/float(len(get_992 ))
		self.get_993  = sum(get_993 )/float(len(get_993 ))
		self.get_994  = sum(get_994 )/float(len(get_994 ))
		self.get_995  = sum(get_995 )/float(len(get_995 ))
		self.get_996  = sum(get_996 )/float(len(get_996 ))
		self.get_997  = sum(get_997 )/float(len(get_997 ))
		self.get_998  = sum(get_998 )/float(len(get_998 ))
		self.get_999  = sum(get_999 )/float(len(get_999 ))
		self.get_9991 = sum(get_9991)/float(len(get_9991))
		self.get_9992 = sum(get_9992)/float(len(get_9992))
		self.get_9993 = sum(get_9993)/float(len(get_9993))
		self.get_9994 = sum(get_9994)/float(len(get_9994))
		self.get_9995 = sum(get_9995)/float(len(get_9995))
		self.get_9996 = sum(get_9996)/float(len(get_9996))
		self.get_9997 = sum(get_9997)/float(len(get_9997))
		self.get_9998 = sum(get_9998)/float(len(get_9998))
		self.get_9999 = sum(get_9999)/float(len(get_9999))
