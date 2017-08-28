import base64
import multiprocessing
import os
import pprint
import Queue
import re
import sys
import threading
import time
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import ClientLogReader
import RocksDbLogReader


def GetPlotDataFile():
	out_dn = "%s/.output" % os.path.dirname(__file__)
	Util.MkDirs(out_dn)
	# out_fn has avg, 99th, 99.9th, 99.99th and their avg, min, max
	out_fn = "%s/mutant-latency-by-cold-stg-devs-by-sstable-mig-temp-thresholds" % out_dn
	if os.path.exists(out_fn):
		return out_fn

	# This has all statistics of individual experiment. Useful for looking into it
	out_fn_individual = "%s/mutant-latency-by-cold-stg-devs-by-sstable-mig-temp-thresholds-individual" % out_dn

	with Cons.MT("Generating plot data file ..."):
		fn = "%s/work/mutant/misc/rocksdb/log/manifest.yaml" % os.path.expanduser("~")
		manifest_yaml = None
		with open(fn) as fo:
			manifest_yaml = yaml.load(fo)
		#Cons.P(pprint.pformat(manifest_yaml["new_exps"]))
		
		# {stg_dev: {sst_mig_temp_threshold: [LogReaders()] } }
		stgdev_sstmigtempthrds = {}

		exps_root = manifest_yaml["Mutant by slow devs by SSTable migration temperature thresholds"]
		for slow_dev1, v in exps_root.iteritems():
			for sst_mig_temp_threshold, v1 in v.iteritems():
				for simulation_time_begin in v1:
					log_readers = GetLogReaders(simulation_time_begin)
					if log_readers.client.options["fast_dev_path"] != "/mnt/local-ssd1/rocksdb-data":
						raise RuntimeError("Unexpected")
					if slow_dev1 != log_readers.client.options["slow_dev1_path"].split("/")[2]:
						raise RuntimeError("Unexpected")
					if float(log_readers.client.options["memory_limit_in_mb"]) != 2048.0:
						raise RuntimeError("Unexpected")
					sst_mig_temp_threshold = float(sst_mig_temp_threshold)
					if sst_mig_temp_threshold != float(log_readers.client.options["sst_migration_temperature_threshold"]):
						raise RuntimeError("Unexpected")
					if slow_dev1 not in stgdev_sstmigtempthrds:
						stgdev_sstmigtempthrds[slow_dev1] = {}
					if sst_mig_temp_threshold not in stgdev_sstmigtempthrds[slow_dev1]:
						stgdev_sstmigtempthrds[slow_dev1][sst_mig_temp_threshold] = []
					stgdev_sstmigtempthrds[slow_dev1][sst_mig_temp_threshold].append(log_readers)

		# Individual experiment results
		with open(out_fn_individual, "w") as fo:
			fmt = "%17s %10s %8.4f %1s" \
					" %8.6f %8.6f" \
					" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f"
			# I want to add fast/slow dev usage here. Then should I move it to one
			# level up?  This is not exactly the storage cost. So, let's leave it
			# here for now.
			header = Util.BuildHeader(fmt, \
					"simulation_time_begin slow_dev sst_mig_temp_threshold system_overloaded" \
					" fast_stg_dev_size_time_in_GB_month slow_stg_dev_size_time_in_GB_month" \
					" put_avg_ms"  \
					" put_99_ms"   \
					" put_991_ms"  \
					" put_992_ms"  \
					" put_993_ms"  \
					" put_994_ms"  \
					" put_995_ms"  \
					" put_996_ms"  \
					" put_997_ms"  \
					" put_998_ms"  \
					" put_999_ms"  \
					" put_9991_ms" \
					" put_9992_ms" \
					" put_9993_ms" \
					" put_9994_ms" \
					" put_9995_ms" \
					" put_9996_ms" \
					" put_9997_ms" \
					" put_9998_ms" \
					" put_9999_ms" \
					\
					" get_avg_ms"  \
					" get_99_ms"   \
					" get_991_ms"  \
					" get_992_ms"  \
					" get_993_ms"  \
					" get_994_ms"  \
					" get_995_ms"  \
					" get_996_ms"  \
					" get_997_ms"  \
					" get_998_ms"  \
					" get_999_ms"  \
					" get_9991_ms" \
					" get_9992_ms" \
					" get_9993_ms" \
					" get_9994_ms" \
					" get_9995_ms" \
					" get_9996_ms" \
					" get_9997_ms" \
					" get_9998_ms" \
					" get_9999_ms"
					)
			fo.write("%s\n" % header)
			for stg_dev, v in stgdev_sstmigtempthrds.iteritems():
				for sst_mig_temp_threshold, logs in sorted(v.iteritems()):
					for log in logs:
						cl = log.client
						rl = log.rocksdb
						#Cons.P(pprint.pformat(vars(cl)))
						fo.write((fmt + "\n") % (
							cl.simulation_time_begin, stg_dev, sst_mig_temp_threshold, ("T" if cl.system_overloaded else "F")
							, rl.storage_sizetime["t0"], rl.storage_sizetime["t1"]
							, (cl.put_avg  / 1000.0)
							, (cl.put_99   / 1000.0)
							, (cl.put_991  / 1000.0)
							, (cl.put_992  / 1000.0)
							, (cl.put_993  / 1000.0)
							, (cl.put_994  / 1000.0)
							, (cl.put_995  / 1000.0)
							, (cl.put_996  / 1000.0)
							, (cl.put_997  / 1000.0)
							, (cl.put_998  / 1000.0)
							, (cl.put_999  / 1000.0)
							, (cl.put_9991 / 1000.0)
							, (cl.put_9992 / 1000.0)
							, (cl.put_9993 / 1000.0)
							, (cl.put_9994 / 1000.0)
							, (cl.put_9995 / 1000.0)
							, (cl.put_9996 / 1000.0)
							, (cl.put_9997 / 1000.0)
							, (cl.put_9998 / 1000.0)
							, (cl.put_9999 / 1000.0)

							, (cl.get_avg  / 1000.0)
							, (cl.get_99   / 1000.0)
							, (cl.get_991  / 1000.0)
							, (cl.get_992  / 1000.0)
							, (cl.get_993  / 1000.0)
							, (cl.get_994  / 1000.0)
							, (cl.get_995  / 1000.0)
							, (cl.get_996  / 1000.0)
							, (cl.get_997  / 1000.0)
							, (cl.get_998  / 1000.0)
							, (cl.get_999  / 1000.0)
							, (cl.get_9991 / 1000.0)
							, (cl.get_9992 / 1000.0)
							, (cl.get_9993 / 1000.0)
							, (cl.get_9994 / 1000.0)
							, (cl.get_9995 / 1000.0)
							, (cl.get_9996 / 1000.0)
							, (cl.get_9997 / 1000.0)
							, (cl.get_9998 / 1000.0)
							, (cl.get_9999 / 1000.0)
							))
				fo.write("\n")
		Cons.P("Created %s %d" % (out_fn_individual, os.path.getsize(out_fn_individual)))

		with open(out_fn, "w") as fo:
			fmt = "%10s %8.4f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f"
			header = Util.BuildHeader(fmt, \
					"slow_dev sst_mig_temp_threshold" \
					\
					" put_avg_ms_avg put_avg_ms_min put_avg_ms_max" \
					" put_99_ms_99 put_99_ms_min put_99_ms_max" \
					" put_999_ms_999 put_999_ms_min put_999_ms_max" \
					" put_9999_ms_9999 put_9999_ms_min put_9999_ms_max" \
					\
					" get_avg_ms_avg get_avg_ms_min get_avg_ms_max" \
					" get_99_ms_99 get_99_ms_min get_99_ms_max" \
					" get_999_ms_999 get_999_ms_min get_999_ms_max" \
					" get_9999_ms_9999 get_9999_ms_min get_9999_ms_max" \
					)
			fo.write("%s\n" % header)
			for stg_dev, v in stgdev_sstmigtempthrds.iteritems():
				for sst_mig_temp_threshold, logs in sorted(v.iteritems()):
					#Cons.P("(%s %f)" % (stg_dev, sst_mig_temp_threshold))
					ls = LatencyStat(logs)
					if ls.NumExps() == 0:
						continue
					fo.write((fmt + "\n") % (
						stg_dev, sst_mig_temp_threshold
						, ls.PutAvgAvg() , ls.PutAvgMin() , ls.PutAvgMax()
						, ls.Put99Avg()  , ls.Put99Min()  , ls.Put99Max()
						, ls.Put999Avg() , ls.Put999Min() , ls.Put999Max()
						, ls.Put9999Avg(), ls.Put9999Min(), ls.Put9999Max()
						, ls.GetAvgAvg() , ls.GetAvgMin() , ls.GetAvgMax()
						, ls.Get99Avg()  , ls.Get99Min()  , ls.Get99Max()
						, ls.Get999Avg() , ls.Get999Min() , ls.Get999Max()
						, ls.Get9999Avg(), ls.Get9999Min(), ls.Get9999Max()
						))
				fo.write("\n")
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))
	return out_fn


# {simulation_time_begin: ClientLogReader() }
_client_log_reader_cache = {}
_client_log_reader_cache_lock = threading.Lock()

# Single-threaded vesion is faster!
#   http://stackoverflow.com/questions/10789042/python-multi-threading-slower-than-serial
#def PrepareClientLogReaders(exp_list):
#	for simulation_time_begin in exp_list:
#		cl = ClientLogReader(simulation_time_begin)
#		_client_log_reader_cache[simulation_time_begin] = cl
#
#
#_q = None
#def PrepareClientLogReadersMultithreaded(exp_list):
#	global _q
#	_q = Queue.Queue()
#	for simulation_time_begin in exp_list:
#		_q.put(simulation_time_begin)
#
#	num_cpus = multiprocessing.cpu_count()
#	Cons.P("num_cpus=%d" % num_cpus)
#
#	threads = []
#	for i in range(num_cpus):
#		t = threading.Thread(target=_PrepareClientLogReaders)
#		threads.append(t)
#	for t in threads:
#		t.start()
#	for t in threads:
#		t.join()
#
#
#def _PrepareClientLogReaders():
#	global _q
#	global _client_log_reader_cache
#	global _client_log_reader_cache_lock
#
#	while True:
#		try:
#			simulation_time_begin = _q.get(block=False)
#			Cons.P("tid=%s simulation_time_begin=%s" % (threading.current_thread().name, simulation_time_begin))
#
#			cl = ClientLogReader(simulation_time_begin)
#			with _client_log_reader_cache_lock:
#				_client_log_reader_cache[simulation_time_begin] = cl
#		except Queue.Empty as e:
#			Cons.P(e)
#			break

# {simulation_time_begin: RocksdbLogReader() }
_rocksdb_log_reader_cache = {}
_rocksdb_log_reader_cache_lock = threading.Lock()

def GetLogReaders(simulation_time_begin):
	client_log_reader = None
	rocksdb_log_reader = None
	
	with _client_log_reader_cache_lock:
		if simulation_time_begin in _client_log_reader_cache:
			client_log_reader = _client_log_reader_cache[simulation_time_begin]
	if client_log_reader is None:
		client_log_reader = ClientLogReader.ClientLogReader(simulation_time_begin)
		with _client_log_reader_cache_lock:
			_client_log_reader_cache[simulation_time_begin] = client_log_reader

	with _rocksdb_log_reader_cache_lock:
		if simulation_time_begin in _rocksdb_log_reader_cache:
			rocksdb_log_reader = _rocksdb_log_reader_cache[simulation_time_begin]
	if rocksdb_log_reader is None:
		rocksdb_log_reader = RocksDbLogReader.RocksDbLogReader(simulation_time_begin)
		with _rocksdb_log_reader_cache_lock:
			_rocksdb_log_reader_cache[simulation_time_begin] = rocksdb_log_reader

	return LogReaders(client_log_reader, rocksdb_log_reader)


class LogReaders:
	def __init__(self, cl, rl):
		self.client = cl
		self.rocksdb = rl


class LatencyStat:
	def __init__(self, logs):
		self.put_avg  = []
		self.put_99   = []
		self.put_999  = []
		self.put_9999 = []
		self.get_avg  = []
		self.get_99   = []
		self.get_999  = []
		self.get_9999 = []
		for log in logs:
			cl = log.client
			# Exclude overloaded experiments
			if cl.system_overloaded:
				continue
			self.put_avg .append(cl.put_avg )
			self.put_99  .append(cl.put_99  )
			self.put_999 .append(cl.put_999 )
			self.put_9999.append(cl.put_9999)
			self.get_avg .append(cl.get_avg )
			self.get_99  .append(cl.get_99  )
			self.get_999 .append(cl.get_999 )
			self.get_9999.append(cl.get_9999)
		if len(self.put_avg) == 0:
			return
		# Exclude one outlier: the experiment with the biggest number
		if False:
			self.put_avg .remove(max(self.put_avg ))
			self.put_99  .remove(max(self.put_99  ))
			self.put_999 .remove(max(self.put_999 ))
			self.put_9999.remove(max(self.put_9999))
			self.get_avg .remove(max(self.get_avg ))
			self.get_99  .remove(max(self.get_99  ))
			self.get_999 .remove(max(self.get_999 ))
			self.get_9999.remove(max(self.get_9999))

	def NumExps(self):
		return len(self.put_avg)

	def PutAvgAvg(self):
		return float(sum(self.put_avg))  / len(self.put_avg) / 1000.0
	def PutAvgMax(self):
		return max(self.put_avg) / 1000.0
	def PutAvgMin(self):
		return min(self.put_avg) / 1000.0
	def Put99Avg(self):
		return float(sum(self.put_99))   / len(self.put_99) / 1000.0
	def Put99Min(self):
		return min(self.put_99) / 1000.0
	def Put99Max(self):
		return max(self.put_99) / 1000.0
	def Put999Avg(self):
		return float(sum(self.put_999))  / len(self.put_999) / 1000.0
	def Put999Min(self):
		return min(self.put_999) / 1000.0
	def Put999Max(self):
		return max(self.put_999) / 1000.0
	def Put9999Avg(self):
		return float(sum(self.put_9999)) / len(self.put_9999) / 1000.0
	def Put9999Min(self):
		return min(self.put_9999) / 1000.0
	def Put9999Max(self):
		return max(self.put_9999) / 1000.0

	def GetAvgAvg(self):
		return float(sum(self.get_avg))  / len(self.get_avg) / 1000.0
	def GetAvgMax(self):
		return max(self.get_avg) / 1000.0
	def GetAvgMin(self):
		return min(self.get_avg) / 1000.0
	def Get99Avg(self):
		return float(sum(self.get_99))   / len(self.get_99) / 1000.0
	def Get99Min(self):
		return min(self.get_99) / 1000.0
	def Get99Max(self):
		return max(self.get_99) / 1000.0
	def Get999Avg(self):
		return float(sum(self.get_999))  / len(self.get_999) / 1000.0
	def Get999Min(self):
		return min(self.get_999) / 1000.0
	def Get999Max(self):
		return max(self.get_999) / 1000.0
	def Get9999Avg(self):
		return float(sum(self.get_9999)) / len(self.get_9999) / 1000.0
	def Get9999Min(self):
		return min(self.get_9999) / 1000.0
	def Get9999Max(self):
		return max(self.get_9999) / 1000.0
