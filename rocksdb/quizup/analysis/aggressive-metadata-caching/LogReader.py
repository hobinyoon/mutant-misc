import base64
import multiprocessing
import os
import pprint
import Queue
import re
import sys
import time
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import ClientLogReader


def GetFileLatencyByMetadataCachingByStgDevs():
	out_dn = "%s/.output" % os.path.dirname(__file__)
	Util.MkDirs(out_dn)
	# out_fn has avg, 99th, 99.9th, 99.99th and their avg, min, max
	out_fn = "%s/rocksdb-latency-by-metadata-caching-by-stg-devs" % out_dn
	# This has all statistics of individual experiment. Useful for looking into it
	out_fn_individual = "%s/rocksdb-latency-by-metadata-caching-by-stg-devs-individual" % out_dn

	if os.path.exists(out_fn) and os.path.exists(out_fn_individual):
		# Show the latency reduction stat
		with open(out_fn) as fo:
			start_print = False
			for line in fo:
				if start_print:
					Cons.P(line)
				else:
					if line.startswith("# # Latency reduction stat:"):
						start_print = True
						Cons.P(line)
		return (out_fn, out_fn_individual)

	with Cons.MT("Generating plot data file ..."):
		fn = "%s/work/mutant/misc/rocksdb/log/manifest.yaml" % os.path.expanduser("~")
		manifest_yaml = None
		with open(fn) as fo:
			manifest_yaml = yaml.load(fo)
		
		# {stg_dev: {metadata_caching: [LogReaders()] } }
		stgdev_mdcaching_logreaders = {}

		exp_list_root = manifest_yaml["Unmodified RocksDB with and without metadata caching. On EC2"]
		for exp_conf, v in exp_list_root.iteritems():
			metadata_caching = (exp_conf == "With aggressive metadata caching")
			for stg_dev, v1 in v.iteritems():
				for simulation_time_begin in v1:
					#Cons.P("%s %s %s" % (metadata_caching, stg_dev, simulation_time_begin))
					log_readers = GetLogReaders(simulation_time_begin)
					if stg_dev != log_readers.client.options["fast_dev_path"].split("/")[2]:
						raise RuntimeError("Unexpected")
					if metadata_caching != ((log_readers.client.options["cache_filter_index_at_all_levels"]).lower() == "true"):
						raise RuntimeError("Unexpected")
					if stg_dev not in stgdev_mdcaching_logreaders:
						stgdev_mdcaching_logreaders[stg_dev] = {}
					if metadata_caching not in stgdev_mdcaching_logreaders[stg_dev]:
						stgdev_mdcaching_logreaders[stg_dev][metadata_caching] = []
					stgdev_mdcaching_logreaders[stg_dev][metadata_caching].append(log_readers)

		with open(out_fn_individual, "w") as fo:
			fmt = "%17s %10s %1s %1s" \
					" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f" \
					" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f"
			header = Util.BuildHeader(fmt, \
					"simulation_time_begin slow_dev metadata_caching system_overloaded" \
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
			for stg_dev, v in stgdev_mdcaching_logreaders.iteritems():
				for metadata_caching, logs in sorted(v.iteritems()):
					for log in logs:
						cl = log.client
						rl = log.rocksdb
						#Cons.P(pprint.pformat(vars(cl)))
						fo.write((fmt + "\n") % (
							cl.simulation_time_begin, stg_dev, ("T" if metadata_caching else "F"), ("T" if cl.system_overloaded else "F")
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

		# Latency reduction stat
		fmt1 = "%10s" \
				" %11.6f %11.6f %7.3f" \
				" %11.6f %11.6f %7.3f"
		latency_reduction_stat_str = []
		latency_reduction_stat_str.append("# Latency reduction stat:")
		for s in Util.BuildHeader(fmt1, "stg_dev" \
				" unmodified_rocksdb_put_avg_in_ms with_aggr_caching_put_avg_in_ms latency_reduction_in_percent" \
				" unmodified_rocksdb_get_avg_in_ms with_aggr_caching_get_avg_in_ms latency_reduction_in_percent" \
				).split("\n"):
			latency_reduction_stat_str.append(s)
		for stg_dev in ["local-ssd1", "ebs-gp2", "ebs-st1", "ebs-sc1"]:
			mdcaching_logs = stgdev_mdcaching_logreaders[stg_dev]
			unmodified = LatencyStat(mdcaching_logs[False])
			with_caching = LatencyStat(mdcaching_logs[True])
			latency_reduction_stat_str.append(fmt1 % (stg_dev \
					, unmodified.PutAvgAvg(), with_caching.PutAvgAvg() \
					, (100.0 * (unmodified.PutAvgAvg() - with_caching.PutAvgAvg()) / unmodified.PutAvgAvg())
					, unmodified.GetAvgAvg(), with_caching.GetAvgAvg() \
					, (100.0 * (unmodified.GetAvgAvg() - with_caching.GetAvgAvg()) / unmodified.GetAvgAvg())
					))
		for s in latency_reduction_stat_str:
			Cons.P(s)

		with open(out_fn, "w") as fo:
			fmt = "%10s %1s" \
					" %9.3f %9.3f %9.3f" \
					" %9.3f %9.3f %9.3f" \
					" %9.3f %9.3f %9.3f" \
					" %9.3f %9.3f %9.3f" \
					" %9.3f %9.3f %9.3f" \
					" %9.3f %9.3f %10.3f" \
					" %10.3f %10.3f %11.3f" \
					" %10.3f %10.3f %11.3f"
			header = Util.BuildHeader(fmt, \
					"slow_dev metadata_caching" \
					\
					" put_avg_ms_avg put_avg_ms_min put_avg_ms_max" \
					" put_99_ms_avg put_99_ms_min put_99_ms_max" \
					" put_999_ms_avg put_999_ms_min put_999_ms_max" \
					" put_9999_ms_avg put_9999_ms_min put_9999_ms_max" \
					\
					" get_avg_ms_avg get_avg_ms_min get_avg_ms_max" \
					" get_99_ms_avg get_99_ms_min get_99_ms_max" \
					" get_999_ms_avg get_999_ms_min get_999_ms_max" \
					" get_9999_ms_avg get_9999_ms_min get_9999_ms_max" \
					)
			fo.write("%s\n" % header)
			for stg_dev, v in stgdev_mdcaching_logreaders.iteritems():
				for md_caching, logs in sorted(v.iteritems()):
					ls = LatencyStat(logs)
					if ls.NumExps() == 0:
						continue
					fo.write((fmt + "\n") % (
						stg_dev, ("T" if md_caching else "F")
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
			for s in latency_reduction_stat_str:
				fo.write("# %s\n" % s)

		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))

	return (out_fn, out_fn_individual)


_client_log_reader_cache = {}
_rocksdb_log_reader_cache = {}

def GetLogReaders(simulation_time_begin):
	global _client_log_reader_cache
	client_log_reader = None
	if simulation_time_begin in _client_log_reader_cache:
		client_log_reader = _client_log_reader_cache[simulation_time_begin]
	if client_log_reader is None:
		client_log_reader = ClientLogReader.ClientLogReader(simulation_time_begin)
		_client_log_reader_cache[simulation_time_begin] = client_log_reader

	# We don't need to read rocksdb log here
	global _rocksdb_log_reader_cache
	rocksdb_log_reader = None
	if False:
		if simulation_time_begin in _rocksdb_log_reader_cache:
			rocksdb_log_reader = _rocksdb_log_reader_cache[simulation_time_begin]
		if rocksdb_log_reader is None:
			rocksdb_log_reader = RocksDbLogReader.RocksDbLogReader(simulation_time_begin)
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
