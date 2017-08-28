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
import Conf
import RocksDbLogReader
import StgSizeCost


# Unmodified RocksDb
def GetRocksDbCostLatencyDataFile():
	dn = "%s/.output" % os.path.dirname(__file__)
	fn = "%s/rocksdb-cost-latency" % dn
	if os.path.exists(fn):
		return fn

	rocksdb_stgsizetimecost = StgSizeCost.StgSizetimeCostRocksDb()
	#Cons.P(rocksdb_stgsizetimecost)

	# { stg_dev: Latency() }
	rocksdb_dev_latexp = {}
	exps_root = Conf.Manifest.Get("2-level Mutant latencies by SSTable migration temperature thresholds")
	for stg_dev, exps in {"local-ssd1": exps_root["UnmodifiedRocksDB"]["LocalSsd1"] \
			, "ebs-st1": exps_root["UnmodifiedRocksDB"]["EbsSt1"] \
			}.iteritems():
		if stg_dev not in rocksdb_dev_latexp:
			rocksdb_dev_latexp[stg_dev] = Latency()
		for simulation_time_begin in exps:
			rocksdb_dev_latexp[stg_dev].Add(ClientLogReader.ClientLogReader(simulation_time_begin))

	with open(fn, "w") as fo:
		fmt = "%10s" \
				" %8.5f" \
				" %10.3f %10.3f %10.3f" \
				" %10.3f %10.3f %10.3f"
		fo.write("%s\n" % Util.BuildHeader(fmt, \
				"stg_dev" \
				" cost_$" \
				" lat_put_avg_avg_in_ms lat_put_avg_min_in_ms lat_put_avg_max_in_ms" \
				" lat_get_avg_avg_in_ms lat_get_avg_min_in_ms lat_get_avg_max_in_ms"
				))
		#for stg_dev, exps in reversed(sorted(rocksdb_dev_latexp.iteritems())):
		for stg_dev, exps in rocksdb_dev_latexp.iteritems():

			if stg_dev == "local-ssd1":
				cost = rocksdb_stgsizetimecost.Cost("Sum")
			elif stg_dev == "ebs-st1":
				cost = rocksdb_stgsizetimecost.Cost("Sum") * Conf.StgCost("ebs-st1") / Conf.StgCost("local-ssd1")

			fo.write((fmt + "\n") % (
				stg_dev
				, cost
				, exps.PutAvgAvg()
				, exps.PutAvgMin()
				, exps.PutAvgMax()
				, exps.GetAvgAvg()
				, exps.GetAvgMin()
				, exps.GetAvgMax()
				))
	Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn


def GetMutantCostLatencyDataFile():
	dn = "%s/.output" % os.path.dirname(__file__)
	fn = "%s/mutant-cost-latency" % dn
	if os.path.exists(fn):
		return fn

	stg_sizetime_cost_by_sst_mig_temp_thresholds = StgSizeCost.StgSizetimeCostMutant()
	#Cons.P(stg_sizetime_cost_by_sst_mig_temp_thresholds)

	exps_root = Conf.Manifest.Get("2-level Mutant latencies by SSTable migration temperature thresholds")

	# { metadata_caching: { sst_mig_temp_threshold: Latency() } }
	mdcaching_smtt_latexps = {}

	for md_caching, exps in {True: exps_root["Mutant"]["MetadataCachingOn"] \
			, False: exps_root["Mutant"]["MetadataCachingOff"]}.iteritems():
		#Cons.P("%s %s" % (md_caching, exps))

		for sst_mig_temp_threshold, v in exps.iteritems():
			sst_mig_temp_threshold = float(sst_mig_temp_threshold)
			for simulation_time_begin in v:
				if md_caching not in mdcaching_smtt_latexps:
					mdcaching_smtt_latexps[md_caching] = {}

				if sst_mig_temp_threshold not in mdcaching_smtt_latexps[md_caching]:
					mdcaching_smtt_latexps[md_caching][sst_mig_temp_threshold] = Latency()
				mdcaching_smtt_latexps[md_caching][sst_mig_temp_threshold].Add(ClientLogReader.ClientLogReader(simulation_time_begin))
	
	with open(fn, "w") as fo:
		fmt = "%1s %17s" \
				" %8.5f" \
				" %10.3f %10.3f %10.3f" \
				" %10.3f %10.3f %10.3f"
		fo.write("%s\n" % Util.BuildHeader(fmt, \
				"md_caching sst_mig_temp_threshold" \
				" cost_$" \
				" lat_put_avg_avg_in_ms lat_put_avg_min_in_ms lat_put_avg_max_in_ms" \
				" lat_get_avg_avg_in_ms lat_get_avg_min_in_ms lat_get_avg_max_in_ms"
				))
		for md_caching, v in mdcaching_smtt_latexps.iteritems():
			for sst_mig_temp_threshold, lat in sorted(v.iteritems()):
				fo.write((fmt + "\n") % (
					("T" if md_caching else "F")
					, sst_mig_temp_threshold
					# Average cost
					, stg_sizetime_cost_by_sst_mig_temp_thresholds[sst_mig_temp_threshold].Cost("Sum")[0]
					, lat.PutAvgAvg()
					, lat.PutAvgMin()
					, lat.PutAvgMax()
					, lat.GetAvgAvg()
					, lat.GetAvgMin()
					, lat.GetAvgMax()
					))
	Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))

	# Mutant latency individual. Useful for filtering out outliers
	# TODO: work on this
	# TODO: do the same thing with unmodified RocksDB
#	fn_lat_individual = "%s/mutant-latency-individual" % fn
#
#	with open(fn_lat_individual, "w") as fo:
#		fmt = "%17s" \
#				" %28s %1s %17s" \
#				" %10.3f %10.3f"
#
#				#" %9.6f %9.6f %9.6f" \
#
#		fo.write("%s\n" % Util.BuildHeader(fmt, \
#				"simulation_time_begin" \
#				" system metadata_caching SSTable_migration_temperature_threshold"
#				" Lat_put_in_ms Lat_get_in_ms"
#				))
#
#		for stg_dev, exps in sorted(rocks_dev_exps.iteritems(), reverse=True):
#			for e in exps.Exps():
#				fo.write((fmt + "\n") % (
#					e[0].simulation_time_begin
#					, ("UnmodifiedRocksDB_%s" % stg_dev)
#					, "-"
#					, "-"
#					, e[0].put_avg
#					, e[0].get_avg
#					))
#
#		for md_caching, v in sorted(mu_mdcaching_smtt_exps.iteritems()):
#			for sst_mig_temp_threshold, mu_exps in sorted(v.iteritems()):
#				for e in mu_exps.Exps():
#					fo.write((fmt + "\n") % (
#						e[0].simulation_time_begin
#						, "Mutant"
#						, ("T" if md_caching else "F")
#						, sst_mig_temp_threshold
#						, e[1].avg_numssts_by_level[0]
#						, e[1].avg_numssts_by_level[1]
#						, e[1].avg_numssts_by_level[2]
#
#						#, e[1].avg_sizetime_by_level[0]
#						#, e[1].avg_sizetime_by_level[1]
#						#, e[1].avg_sizetime_by_level[2]
#
#						, e[1].avg_numssts_by_pathid[0]
#						, e[1].avg_numssts_by_pathid[1]
#						, e[1].avg_numssts_by_pathid[2]
#						, e[1].avg_numssts_by_pathid[3]
#
#						, e[0].put_avg
#						, e[0].get_avg
#						))
#	Cons.P("Created %s %d" % (fn_lat_individual, os.path.getsize(fn_lat_individual)))

	return fn


class Latency:
	def __init__(self):
		self.exps = []
	def Add(self, client_log_reader):
		self.exps.append(client_log_reader)

	def PutAvgAvg(self):
		sum_ = 0.0
		for e in self.exps:
			sum_ += e.put_avg
		return sum_ / len(self.exps)
	def PutAvgMin(self):
		min_ = None
		for e in self.exps:
			if min_ is None:
				min_ = e.put_avg
			else:
				min_ = min(min_, e.put_avg)
		return min_
	def PutAvgMax(self):
		max_ = None
		for e in self.exps:
			if max_ is None:
				max_ = e.put_avg
			else:
				max_ = max(max_, e.put_avg)
		return max_

	def GetAvgAvg(self):
		sum_ = 0.0
		for e in self.exps:
			sum_ += e.get_avg
		return sum_ / len(self.exps)
	def GetAvgMin(self):
		min_ = None
		for e in self.exps:
			if min_ is None:
				min_ = e.get_avg
			else:
				min_ = min(min_, e.get_avg)
		return min_
	def GetAvgMax(self):
		max_ = None
		for e in self.exps:
			if max_ is None:
				max_ = e.get_avg
			else:
				max_ = max(max_, e.get_avg)
		return max_

	# TODO: you may need this for individual stat
	def Exps(self):
		return self.exps
