import bisect
import collections
import datetime
import os
import re
import sys
import traceback

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import CassCompactionLogReader
import Conf
import MutantLogReader
import SstYCord


# {sst_gen: SstLife()}
_sst_lives = None
# {addr: MemtLife()}
_memt_lives = None

def Get():
	global _sst_lives, _memt_lives
	if (_sst_lives is not None) and (_memt_lives is not None):
		return (_sst_lives, _memt_lives)

	(mu_compaction_events, mu_events) = MutantLogReader.Get()

	with Cons.MT("Building MemtLife map and SstLife map ..."):
		_sst_lives = {}
		_memt_lives = {}
		num_sst_reads_before_created = 0

		for me in mu_events.events:
			# me is of type MuEvents.MuEvent()
			#Cons.P(me)

			if me.event == "ResetMon":
				# Conf.ExpStartTime() is already set to me.datetime
				pass
			elif me.event == "Node configuration":
				# Note: may want to add minimal info to the plot later, like exp datetime.
				pass

			# Note: Memt lives and Sst lives can be seletively built, but this is not
			# a bottleneck. I think it's the re parsing part and since a
			# comprehensive checking is made there, it's hard to do a selective
			# parsing.
			elif me.event == "MemtCreated":
				if me.memt_addr in _memt_lives:
					raise RuntimeError("Unexpected")
				_memt_lives[me.memt_addr] = MemtLife(me)
			elif me.event == "MemtDiscard":
				_memt_lives[me.memt_addr].SetDiscarded(me)

			elif me.event in ["SstCreated", "SstOpened"]:
				if me.sst_gen not in _sst_lives:
					sl = SstLife(me.sst_gen)
					_sst_lives[me.sst_gen] = sl
				sl = _sst_lives[me.sst_gen]
				sl.SetOpened(me)

			elif me.event == "SstDeleted":
				_sst_lives[me.sst_gen].SetDeleted(me)
			elif me.event == "TabletAccessStat":
				if me.memt_addr is not None:
					_memt_lives[me.memt_addr].SetAccStat(me)
				# {sst_gen: SstReadStat()}
				#   sst_gen
				#   level
				#   num_reads
				for sst_gen, s in me.sst_reads.iteritems():
					# There are SSTable reads before one is created. Must be missing
					# something. It's okay for now.
					if sst_gen not in _sst_lives:
						#Cons.P("Hmm: Reads to SSTable %d before it is created" % sst_gen)
						num_sst_reads_before_created += 1
						_sst_lives[sst_gen] = SstLife(sst_gen)
					_sst_lives[sst_gen].SetAccStat(me.datetime, s)
			else:
				raise RuntimeError("Unexpected me.event=[%s]" % me.event)

		Cons.P("SSTable level set from read stats not when it's opened: %d times" % SstLife.num_force_set_sst_level)
		Cons.P("SSTable read before created: %d times" % num_sst_reads_before_created)

		_FilterSstablesWoSizeOrLevel()
		_CalcSstHeat()
		SstYCord.Calc(_sst_lives)

		return (_sst_lives, _memt_lives)


def GetSstLives():
	if _sst_lives is not None:
		return _sst_lives

	# If _sst_lives doesn't exist, try loading from an existing result file
	# first.  The resulting _sst_lives may not contain full info, but should be
	# good enough for the SstByLevelsWithHeatAtSpecificTimes or SstHeatmapByTime
	# plot.
	LoadSstLivesFromPlotDataFiles()
	if _sst_lives is not None:
		return _sst_lives

	# If neither sst_lives-in-memory nor sst_lives-in-plot-data exists, get it
	# from parsing the Cassandra log file.
	Get()
	return _sst_lives


def SetExpEndTimeFromSstLives():
	# Use the last heat time
	last_heat_time = None
	for sst_gen, sl in _sst_lives.iteritems():
		t1 = sl.LastHeatTime()
		if t1 is None:
			continue
		last_heat_time = t1 if last_heat_time is None else max(last_heat_time, t1)
	Conf.SetExpFinishTime(last_heat_time.strftime("%y%m%d-%H%M%S.%f")[:-3])


def LoadSstLivesFromPlotDataFiles():
	global _sst_lives
	if _sst_lives is not None:
		return _sst_lives

	fn_sst_info_by_time = "%s/sst-info-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if not os.path.isfile(fn_sst_info_by_time):
		return None

	fn_sst_heat_by_time = "%s/sst-heat-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if not os.path.isfile(fn_sst_heat_by_time):
		return None

	# This is not needed for the by-levels-with-heat plot
	#	"%s/sst-info-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())

	with Cons.MT("Loading Sst lives from (%s, %s) ..." % (fn_sst_info_by_time, fn_sst_heat_by_time)):
		_sst_lives = {}
		with open(fn_sst_info_by_time) as fo:
			for line in fo.readlines():
				if len(line) == 0:
					continue
				if line[0] == "#":
					continue
				line = line.strip()
				#Cons.P(line)
				t = re.split(r" +", line)
				sst_gen = int(t[0])
				sl = SstLife(sst_gen)
				sl.SetInfoFromPlotData(t)
				_sst_lives[sst_gen] = sl

		with open(fn_sst_heat_by_time) as fo:
			sstgen_lines_tokens = {}

			for line in fo.readlines():
				if len(line) == 0:
					continue
				if line[0] == "#":
					continue
				line = line.strip()
				if len(line) == 0:
					continue
				t = re.split(r" +", line)
				if len(t) == 0:
					continue
				sst_gen = int(t[0])
				if sst_gen not in sstgen_lines_tokens:
					sstgen_lines_tokens[sst_gen] = []
				sstgen_lines_tokens[sst_gen].append(t)

			for sstgen, lt in sstgen_lines_tokens.iteritems():
				_sst_lives[sstgen].SetHeatFromPlotData(lt)
		return _sst_lives


def SstInfoByTimeByLevel():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn = "%s/sst-info-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn):
		return fn

	(sst_lives, memt_lives) = MemtSstLife.Get()

	with Cons.MT("Generating Sst info by time by levels data file ..."):
		#with open(fn_m, "w") as fo:
		#	fo.write("%s\n" % MemtLife.Header())
		#	for addr, l in sorted(_memt_lives.iteritems()):
		#		fo.write("%s\n" % l)
		#Cons.P("Created %s %d" % (fn_m, os.path.getsize(fn_m)))

		with open(fn, "w") as fo:
			fo.write("%s\n" % MemtSstLife.SstLife.Header())
			for sst_gen, l in sorted(sst_lives.iteritems()):
				fo.write("%s\n" % l)
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn


# Filter out SSTables without sizes or level, since you can't place them in the
# figure.
def _FilterSstablesWoSizeOrLevel():
	with Cons.MT("Filtering SSTables ...", print_time=False):
		cnt = 0
		for k in _sst_lives.keys():
			if _sst_lives[k].Size() is None:
				del _sst_lives[k]
				cnt += 1
		if cnt > 0:
			Cons.P("Filtered out %s SSTables without sizes" % cnt)

		# Drop SSTables without level info
		cnt = 0
		for sst_gen in _sst_lives.keys():
			if _sst_lives[sst_gen].level is None:
				del _sst_lives[sst_gen]
				cnt += 1
		if cnt > 0:
			Cons.P("Dropped %d SStables that don't have level info" % cnt)
		Cons.P("Total %d SSTables now" % len(_sst_lives))


# Calculate heat of SSTables. Heat = number_of_reads/sec/sstable_size.
# Use 5-sec tumbling window
def _CalcSstHeat():
	with Cons.MT("Calculating Sst heat ..."):
		for sst_gen, sl in _sst_lives.iteritems():
			sl.CalcHeat()
		Cons.P("SstLife.max_heat=%.2f" % SstLife.max_heat)


class MemtLife:
	def __init__(self, me):
		self.addr = me.memt_addr
		self.time_created = me.datetime
		self.time_discarded = None
		self.size = None
		self.size_by_time = {}
		self.num_reads_by_time = {}

	def SetDiscarded(self, me):
		self.time_discarded = me.datetime
		self.size_by_time[me.datetime] = me.memt_size
		if self.size is None:
			self.size = me.memt_size
		else:
			self.size = max(self.size, me.memt_size)

	def SetAccStat(self, me):
		self.size_by_time[me.datetime] = me.memt_size
		if self.size is None:
			self.size = me.memt_size
		else:
			self.size = max(self.size, me.memt_size)
		self.num_reads_by_time[me.datetime] = me.memt_num_reads

	fmt = "%10s %17s %17s %6.0f"

	@staticmethod
	def Header():
		return Util.BuildHeader(MemtLife.fmt, "addr time_created time_discarded size_in_kb")

	def __str__(self):
		# When the size is not available, give some sensible value. Every
		# Memtable has around 121 MiB.
		#if self.size is None:
		#	size = 121000
		#	Cons.P("Hmm... Memtable doesn't have a size. Setting to %d" % size)
		#else:
		#	size = self.size
		if self.size is None:
			raise RuntimeError("Unexpected")

		return MemtLife.fmt % (self.addr
				, self.time_created
				, (Conf.ExpFinishTime() if self.time_discarded is None else self.time_discarded)
				, self.size
				)


class SstLife:
	L1_opened_min = None

	# If you just take the first 500ms time interval heat of the first SSTable,
	# the value is too big, like 7186.35. If you do the 5-sec tumbling window
	# average, the max is like 120.
	#
	# You need to go through all SSTables, since you don't know if it's going
	# to be the first one! You are assuming the "read latest" workload.
	# - At first, I thought using the 5-sec window average of the first
	#   SSTable.
	# - This takes long. Make sure you don't calculate this twice.
	max_heat = None

	def __init__(self, sst_gen):
		self.sst_gen = sst_gen
		self.time_open_early = None
		self.time_open_normal = None
		self.time_deleted = None
		self.size = None
		self.level = None
		self.ts_range = None
		self.key_range = None
		# {datetime: num_reads}
		#   It is the number of reads in the last 500 ms interval
		self.num_reads_by_time = collections.OrderedDict()

		# Heat of the Sstable by 5-sec tumbling windows. I think the key needs to
		# be a simple value, not a tuple, to make bisect() possible.
		#   [ (t0, (t1, heat) ) ]
		# Heat = num_reads / sec / sstable_size_in_mb
		self.heat_by_time = collections.OrderedDict()
		self.max_heat = None

		# Y-coord low in the by-time-by-levels plot grouped by Sst levels. The high
		# cord is low + size.
		self.y_cord_low = None

	def SetOpened(self, me):
		if me.open_reason == "EARLY":
			if self.time_open_early is not None:
				raise RuntimeError("Unexpected")
			self.time_open_early = me.datetime
		elif me.open_reason == "NORMAL":
			if self.time_open_normal is not None:
				raise RuntimeError("Unexpected")
			self.time_open_normal = me.datetime
		else:
			raise RuntimeError("Unexpected")

		self.size = me.size
		self.level = me.level

		if self.level == 1:
			if SstLife.L1_opened_min is None:
				SstLife.L1_opened_min = me.datetime
			else:
				SstLife.L1_opened_min = min(SstLife.L1_opened_min, me.datetime)

		self.ts_range = (me.ts_min, me.ts_max)
		self.key_range = (me.token_first, me.token_last)

	def Opened(self):
		t = []

		if len(self.num_reads_by_time) > 0:
			m = min(self.num_reads_by_time, key=self.num_reads_by_time.get)
			m = (datetime.datetime.strptime(m, "%y%m%d-%H%M%S.%f")
					- datetime.timedelta(milliseconds=Conf.mutant_sst_temp_report_interval_in_ms)) \
							.strftime("%y%m%d-%H%M%S.%f")[:-3]
			t.append(m)

		if self.time_open_early is not None:
			t.append(self.time_open_early)
		if self.time_open_normal is not None:
			t.append(self.time_open_normal)
		m = min(t)
		if m is None:
			raise RuntimeError("Unexpected")
		return m

	def Deleted(self):
		return self.time_deleted

	def Size(self):
		return self.size

	def YcordHigh(self):
		return self.y_cord_low + self.size

	def SetDeleted(self, me):
		self.time_deleted = me.datetime

	num_force_set_sst_level = 0

	def SetAccStat(self, datetime, s):
		if self.level is None:
			#Cons.P("Hmm: Setting SSTable %d level to %d, which wasn't set" % (s.sst_gen, s.level))
			SstLife.num_force_set_sst_level += 1
			self.level = s.level
		else:
			# Check if SSTable levels change at runtime. They don't seem to change.
			if self.level != s.level:
				raise RuntimeError("Unexpected")
		self.num_reads_by_time[datetime] = s.num_reads

	def CalcHeat(self):
		num_reads_prev = 0
		t0 = None
		t1 = None

		# Make tumbling window averages
		for dt, num_reads in self.num_reads_by_time.items():
			t1 = datetime.datetime.strptime(dt, "%y%m%d-%H%M%S.%f")
			if t0 is None:
				t0 = t1 - datetime.timedelta(milliseconds=Conf.mutant_sst_temp_report_interval_in_ms)
			dur = (t1 - t0).total_seconds()
			if dur > Conf.heat_block_time_granularity_in_sec:
				heat = float(num_reads - num_reads_prev) / dur \
						/ (float(self.size) / (1024 * 1024))
				self.heat_by_time[t0] = (t1, heat)
				self.max_heat = heat if self.max_heat is None else max(self.max_heat, heat)
				SstLife.max_heat = heat if SstLife.max_heat is None else max(SstLife.max_heat, heat)
				t0 = t1
				num_reads_prev = num_reads

		# The last one
		if t0 != t1:
			dur = (t1 - t0).total_seconds()
			heat = float(num_reads - num_reads_prev) / dur \
					/ (float(self.size) / (1024 * 1024))
			self.heat_by_time[t0] = (t1, heat)
			self.max_heat = heat if self.max_heat is None else max(self.max_heat, heat)
			SstLife.max_heat = heat if SstLife.max_heat is None else max(SstLife.max_heat, heat)

	def HeatAtTime(self, dt0):
		# http://stackoverflow.com/questions/7934547/python-find-closest-key-in-a-dictionary-from-the-given-input-key
		ind = bisect.bisect_left(self.heat_by_time.keys(), dt0)
		if (ind == 0) or (len(self.heat_by_time) <= ind):
			return None
		#Cons.P("self.sst_gen=%s" % self.sst_gen)
		#Cons.P("dt0=%s" % dt0)
		#Cons.P("len(self.heat_by_time)=%d" % len(self.heat_by_time))
		#Cons.P("ind=%d" % ind)
		#Cons.P(self.heat_by_time.items()[ind])
		return self.heat_by_time.items()[ind][1][1]

	def LastHeatTime(self):
		if len(self.heat_by_time) == 0:
			return None
		# [ (t0, (t1, heat) ) ]
		return self.heat_by_time.items()[-1][1][0]

	def SetYcordLow(self, yl):
		self.y_cord_low = yl

	def SetInfoFromPlotData(self, tokens):
		self.sst_gen = int(tokens[0])
		self.time_open_early = None if tokens[1] == "-" else tokens[1]
		self.time_open_normal = None if tokens[2] == "-" else tokens[2]
		self.time_open_min = None if tokens[3] == "-" else tokens[3]
		self.time_deleted = None if tokens[4] == "-" else tokens[4]
		self.size = int(tokens[5])
		self.level = int(tokens[6])
		self.ts_min = tokens[7]
		self.ts_max = tokens[8]
		ks_first = int(tokens[9])
		ks_last = int(tokens[10])
		self.key_range = (ks_first, ks_last)
		#self.y_cord_low = t[11]
		#self.how_created = t[12]

	def SetHeatFromPlotData(self, line_tokens):
		for tokens in line_tokens:
			#self.sst_gen = tokens[0]
			#self.level = tokens[1]
			t0 = datetime.datetime.strptime(tokens[2], "%y%m%d-%H%M%S.%f")
			t1 = datetime.datetime.strptime(tokens[3], "%y%m%d-%H%M%S.%f")
			#age_in_sec = tokens[4]
			#y0 = tokens[5]
			#y1 = tokens[6]
			heat = float(tokens[7])
			#heat_color = tokens[8]
			#heat_color_hex = tokens[9]

			self.heat_by_time[t0] = (t1, heat)
			self.max_heat = heat if self.max_heat is None else max(self.max_heat, heat)
			SstLife.max_heat = heat if SstLife.max_heat is None else max(SstLife.max_heat, heat)

	_fmt = "%4d" \
			" %17s %17s %17s %17s" \
			" %9s %1s" \
			" %17s %17s" \
			" %20s %20s" \
			" %10s" \
			" %-12s"

	@staticmethod
	def Header():
		return Util.BuildHeader(SstLife._fmt, \
				"sst_gen" \
				" time_open_early time_open_normal time_open_min time_deleted" \
				" size level" \
				" ts_min ts_max" \
				" ks_first ks_last" \
				" y_cord_low" \
				" how_created" \
				)

	def __str__(self):
		try:
			if self.ts_range is None:
				tsr0 = None
				tsr1 = None
			else:
				tsr0 = self.ts_range[0]
				tsr1 = self.ts_range[1]

			if self.key_range is None:
				kr0 = None
				kr1 = None
			else:
				kr0 = self.key_range[0]
				kr1 = self.key_range[1]

			return SstLife._fmt % (
					self.sst_gen
					, "-" if self.time_open_early is None else self.time_open_early
					, self.time_open_normal
					, self.Opened()
					, (Conf.ExpFinishTime() if self.time_deleted is None else self.time_deleted)
					, self.size
					, "-" if self.level is None else self.level
					, tsr0, tsr1
					, kr0, kr1
					, "-" if self.y_cord_low is None else self.y_cord_low
					, str(self.sst_gen) \
							+ str(CassCompactionLogReader.HowCreated(self.sst_gen)).replace("flushed", "F").replace("compacted", "C")
					)
		except TypeError as e:
			Cons.P("TypeError: %d\n%s" % (self.sst_gen, traceback.format_exc()))
			sys.exit(1)

	def __repr__(self):
		return str(self)
