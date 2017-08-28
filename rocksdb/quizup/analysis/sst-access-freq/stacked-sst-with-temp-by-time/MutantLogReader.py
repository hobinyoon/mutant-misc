import os
import pickle
import pprint
import re
import sys
import traceback

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

# TODO: won't need this
#import CassCompactionLogReader

import RocksdbLogReader
import Conf
import Util0


_mce = None
_me = None
def Get():
	# TODO: Take an input parameter as exp_starttime. Look for the start of an
	# experiment in the time range [exp_starttime, exp_starttime + 10 sec).

	global _mce, _me
	if (_mce is not None) and (_me is not None):
		return (_mce, _me)

	with Cons.MT("Getting Mutant logs (Cassandra system log and compaction log) ..."):
		raise RuntimeError("Implement")
		# Get Cassandra log first to set the exp start time, which
		# CassCompactionLogReader uses to keep the log.
		RocksdbLogReader.Get()

		_mce = CassCompactionLogReader.Get()
		_me = MuEvents()
		return (_mce, _me)

class MuEvents:
	def __init__(self):
		# [MuEvent()]
		self.events = []
		lines = RocksdbLogReader.Get()

		with Cons.MT("Parsing Mutant logs line by line ..."):
			for line in lines:
				try:
					mo = self._ParseLine(line)
					if mo is None:
						continue
					self.events.append(MuEvents.MuEvent(mo, line))
				except Exception as e:
					Cons.P("e=[%s]" \
							"\nline=[%s]" \
							"\n%s" % (e, line, traceback.format_exc()))
					sys.exit(1)
			# Set experiment end datetime
			Conf.SetExpFinishTime(self.events[-1].datetime)

	def _ParseLine(self, line):
		if "Mutant" not in line:
			return None

		# Regex doesn't need to be pre-compiled for performance optimization. Interesting.
		# - http://stackoverflow.com/questions/452104/is-it-worth-using-pythons-re-compile

		# Note: can use this later
		# INFO  [main] 2016-09-20 00:45:18,661 Config.java:470 - Node configuration:
		if re.match(r"INFO  \[main\]" \
				" \d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d Config.java:\d+" \
				" - (?P<event>Node configuration):.*", line):
			return None

		# WARN  [main] 2016-09-20 02:20:39,251 MemSsTableAccessMon.java:116 - Mutant: Node configuration
		mo = re.match(r"WARN  \[(main|MigrationStage:\d+)\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+" \
				" - Mutant: (?P<event>Node configuration):" \
				"(?P<node_config>.*)" \
				, line)
		if mo is not None:
			return mo

		# WARN  [main] 2016-09-20 01:42:56,003 CassandraDaemon.java:575 - Mutant: CassandraDaemon activate
		if re.match(r"WARN  \[main\] \d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d CassandraDaemon.java:\d+ - Mutant: CassandraDaemon activate", line):
			return None

		# WARN  [main] 2016-09-20 02:20:39,250 MemSsTableAccessMon.java:115 - Mutant: ResetMon
		mo = re.match(r"WARN  \[(main|MigrationStage:\d+)\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ -" \
				" Mutant: (?P<event>ResetMon)", line)
		if mo is not None:
			return mo

		# WARN  [MemSsTAccMon] 2016-09-20 15:03:02,464 MemSsTableAccessMon.java:362 - Mutant: TabletAccessStat Memtable-usertable@1180686059(1.134MiB serialized bytes, 1000 ops, 1%/0% of on/off-heap limit)-22
		mo = re.match(r"WARN  \[MemSsTAccMon\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ - Mutant: (?P<event>TabletAccessStat)" \
				"( Memtable-usertable@(?P<memt_addr>\d+)\((?P<memt_size>(\d|\.)+(K|M)iB) serialized bytes," \
				" \d+ ops," \
				" \d+%/\d+% of on/off-heap limit\)-(?P<memt_num_reads>\d+))*" \
				"(?P<sst_stat>( .+)*)" \
				, line)
		if mo is not None:
			return mo

		# WARN  [main] 2016-09-20 15:59:38,611 MemSsTableAccessMon.java:227 - Mutant: MemtCreated Memtable-usertable@2145909353(0.000KiB serialized bytes, 0 ops, 0%/0% of on/off-heap limit)
		mo = re.match(r"WARN  \[(main|MigrationStage:\d+|SlabPoolCleaner)\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ - Mutant:" \
				" (?P<event>MemtCreated) Memtable-usertable@(?P<memt_addr>\d+)" \
				"\((?P<memt_size>(\d|\.)+(K|M)iB) serialized bytes, \d+ ops, \d+%/\d+% of on/off-heap limit\)" \
				, line)
		if mo is not None:
			return mo

		# WARN  [MemtableReclaimMemory:2] 2016-09-20 15:56:35,133 MemSsTableAccessMon.java:250 - Mutant: MemtDiscard Memtable-usertable@19061575(1.192MiB serialized bytes, 1003 ops, 0%/0% of on/off-heap limit)
		mo = re.match(r"WARN  \[MemtableReclaimMemory:\d+]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ - Mutant:" \
				" (?P<event>MemtDiscard) Memtable-usertable@(?P<memt_addr>\d+)" \
				"\((?P<memt_size>(\d|\.)+(K|M)iB) serialized bytes, \d+ ops, \d+%/\d+% of on/off-heap limit\)" \
				, line)
		if mo is not None:
			return mo

		# WARN  [SSTableBatchOpen:3] 2016-11-02 15:55:31,335 MemSsTableAccessMon.java:261 - Mutant: SstOpened descriptor=/mnt/local-ssd1/cassandra-data/ycsb/usertable-488da08084bf11e6ad9963c053f92bbd/mc-2679-big openReason=NORMAL bytesOnDisk()=53409152 level=0 minTimestamp=160927-235609.677 maxTimestamp=160927-235905.520 first.getToken()=-9222971268524157071 last.getToken()=9221592145284702466
		mo = re.match(r"WARN  \[(MemtableFlushWriter:\d+|CompactionExecutor:\d+|SSTableBatchOpen:\d+)\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ - Mutant:" \
				" (?P<event>(SstCreated|SstOpened))" \
				" descriptor=/mnt/local-ssd1/cassandra-data/ycsb/usertable-\w+/mc-(?P<sst_gen>\d+)-big" \
				" openReason=(?P<open_reason>\w+)" \
				" bytesOnDisk\(\)=(?P<size>\d+)" \
				" level=(?P<level>\d+)" \
				" minTimestamp=(?P<ts_min>[\d\.\-]+)" \
				" maxTimestamp=(?P<ts_max>[\d\.\-]+)" \
				" first.getToken\(\)=(?P<token_first>[\d\-]+)" \
				" last.getToken\(\)=(?P<token_last>[\d\-]+)" \
				".*" \
				, line)
		if mo is not None:
			return mo

		# WARN  [NonPeriodicTasks:1] 2016-09-25 21:30:05,138 MemSsTableAccessMon.java:293 - Mutant: SstDeleted /mnt/local-ssd1/cassandra-data/ycsb/usertable-24e13d30836711e698d3358e3dfbc638/mc-1-big
		mo = re.match(r"WARN  \[NonPeriodicTasks:\d]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ - Mutant: (?P<event>SstDeleted)" \
				" /mnt/local-ssd1/cassandra-data/ycsb/usertable-(\w+)/mc-(?P<sst_gen>\d+)-big" \
				, line)
		if mo is not None:
			return mo

		raise RuntimeError("Unexpected [%s]" % line)

	class MuEvent:
		def __init__(self, mo, line):
			# Keep the raw line for debugging
			self.line = line

			self.datetime = Util0.ShortDateTime(mo.group("datetime"))
			self.event = mo.group("event")

			if self.event == "TabletAccessStat":
				ma = mo.group("memt_addr")
				self.memt_addr = None if ma is None else int(ma)

				self.memt_size = toKiB(mo.group("memt_size"))
				self.memt_num_reads = mo.group("memt_num_reads")
				# {sst_gen: SstReadStat()}
				self.sst_reads = {}
				if len(mo.group("sst_stat")) > 0:
					#  01:22452 02:4077 03:2
					tokens = mo.group("sst_stat").split(" ")
					for t in tokens:
						if len(t) == 0:
							continue
						srs = MuEvents.SstReadStat(t)
						self.sst_reads[srs.sst_gen] = srs
				# TODO: Gather events by sstable ID.
			elif self.event == "MemtCreated":
				self.memt_addr = int(mo.group("memt_addr"))
				self.memt_size = toKiB(mo.group("memt_size"))
			elif self.event == "MemtDiscard":
				self.memt_addr = int(mo.group("memt_addr"))
				self.memt_size = toKiB(mo.group("memt_size"))
			elif self.event == "SstCreated" or self.event == "SstOpened":
				self.sst_gen = int(mo.group("sst_gen"))
				self.open_reason = mo.group("open_reason")
				self.size = int(mo.group("size"))
				self.level = int(mo.group("level"))
				self.ts_min = mo.group("ts_min")
				self.ts_max = mo.group("ts_max")
				self.token_first = int(mo.group("token_first"))
				self.token_last = int(mo.group("token_last"))
			elif self.event == "SstDeleted":
				self.sst_gen = int(mo.group("sst_gen"))
			elif self.event == "ResetMon":
				pass
			elif self.event == "Node configuration":
				self.node_config = MuEvents.NodeConfig(mo.group("node_config"))
			else:
				raise RuntimeError("Unexpected mo=[%s] [%s]" % (mo, str(self)))

		def __str__(self):
			return pprint.pformat(vars(self))

		# I wonder if this is slowing the "pickle"ing time. Probably not. Then, how
		# would unpickle know how to unpikcle?
		def __repr__(self):
			return pprint.pformat(vars(self))


	class NodeConfig:
		def __init__(self, nc_str):
			#t = nc_str.node_config.split("; ")
			#Cons.P(pprint.pformat(t))
			#
			# It has other useful info as well. Just print out mutant options for now.
			#
			# Not sure if I can use a library for this. Not json. Doesn't look like
			# "pickle"d either.
			#
			# org.apache.cassandra.config.MutantOptions@36bc55de[migrate_sstables=false,sst_migration_decision_interval_in_ms=100,sst_tempmon_time_window_in_sec=10.0,sst_tempmon_threshold_num_per_sec=1.0,cold_storage_dir=/mnt/cold-storage/mtdb-cold,tablet_access_stat_report_interval_in_ms=200]
			mo1 = re.match(r".*org.apache.cassandra.config.MutantOptions@\w+" \
					"\[(?P<mu_config>[\w\.,_=/-]+)\].*" \
					, nc_str)
			if mo1 is None:
				raise RuntimeError("Unexpected nc_str=[%s]" % nc_str)
			#Cons.P(mo1.group("mu_config"))
			c = mo1.group("mu_config")
			t = c.split(",")
			self.conf = {}
			for t1 in t:
				t2 = t1.split("=")
				self.conf[t2[0]] = t2[1]
			#Cons.P(pprint.pformat(self.conf))

		def __str__(self):
			return pprint.pformat(vars(self))

		def __repr__(self):
			return pprint.pformat(vars(self))


	class SstReadStat:
		def __init__(self, s):
			t = re.split(r"[:,]", s)
			self.sst_gen = int(t[0])
			self.level = int(t[1])
			# Number of reads to the data file
			self.num_reads = int(t[2])

		def __str__(self):
			return pprint.pformat(vars(self))

		def __repr__(self):
			return pprint.pformat(vars(self))


# TODO: Need to plot system monitor stats too

# Conver MiB to KiB. Input format: 1.134MiB
def toKiB(s):
	if s is None:
		return None

	if s.endswith("KiB"):
		return float(s[0:-3])
	if s.endswith("MiB"):
		return float(s[0:-3]) * 1024
	raise RuntimeError("Unexpected s=[%s]" % s)
