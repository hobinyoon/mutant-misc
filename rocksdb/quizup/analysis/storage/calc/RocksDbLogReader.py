import copy
import datetime
import math
import os
import pprint
import re
import sys
import zipfile

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import SimTime


def CalcStorageCost():
	_BuildMemtSstLives()

	_CalcStorageCost()
	_sst_lives = None


# {sst_id: SstLife()}
_sst_lives = None

# For setting the levels.
_jobid_sstlives = {}

# Read log and parse events: SSTable creation, deletion, accessed, levels,
# how_created (if needed)
#
# We don't analyze memtable accesses. RocksDB log has the creation times and
# number.  Haven't looked at how to log them or relate them with the address.
#_memt_lives = None
def _BuildMemtSstLives():
	with Cons.MT("Building memt and sst lives ..."):
		#global _memt_lives
		global _sst_lives
		#_memt_lives = {}
		_sst_lives = {}

		dn = "%s/work/mutant/misc/rocksdb/log/rocksdb" % os.path.expanduser("~")
		fn = "%s/%s" % (dn, Conf.Get("simulation_time_begin"))
		if not os.path.isfile(fn):
			fn_7z = "%s.7z" % fn
			if not os.path.isfile(fn_7z):
				raise RuntimeError("Unexpected")
			Util.RunSubp("cd %s && 7z e %s" % (dn, fn_7z))
		if not os.path.isfile(fn):
			raise RuntimeError("Unexpected")

		line_no = 0
		with open(fn) as fo:
			for line in fo:
				line_no += 1
				# It's fast enough and often times excuted in parallel. No need to show the progress.
				if False:
					if line_no % 100 == 0:
						Cons.ClearLine()
						Cons.Pnnl("Processing line %d" % line_no)

				# Not needed for storage cost calculation
				#
				# 2016/12/21-02:17:14.329266 7f702d7fa700 EVENT_LOG_v1 {"time_micros":
				# 1482304634329023, "mutant_table_acc_cnt": {"memt":
				# "0x7f69fc00c350:51723 0x7f6bec011200:26942", "sst": "1069:0:30.123:20.123
				# 1059:980:30.123:20.123"}
				#mo = re.match(r".+ EVENT_LOG_v1 {\"time_micros\": (?P<time_micros>\d+)" \
				#		", \"mutant_table_acc_cnt\": {(\"memt\": \"(?P<memt_acc_cnt>(\w|\d|:| )+)\")?" \
				#		"(, )?" \
				#		"(\"sst\": \"(?P<sst_acc_cnt>(\w|\d|:|-|\.| )+)\")?" \
				#		"}" \
				#		".*"
				#		, line)
				#if mo is not None:
				#	_SetTabletAccess(mo)
				#	continue
				
				# 2016/12/21-01:27:40.840324 7f702dffb700 EVENT_LOG_v1 {"time_micros":
				# 1482301660840289, "cf_name": "default", "job": 4, "event":
				# "table_file_creation", "file_number": 15, "file_size": 67569420,
				# "path_id": 0, "table_properties": {"data_size": 67110556, "index_size": 458020,
				# "filter_size": 0, "raw_key_size": 1752468, "raw_average_key_size": 25,
				# "raw_value_size": 65132550, "raw_average_value_size": 966,
				# "num_data_blocks": 16857, "num_entries": 67425, "filter_policy_name":
				# "", "reason": kCompaction, "kDeletedKeys": "0", "kMergeOperands": "0"}}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d)" \
						".+ EVENT_LOG_v1 {\"time_micros\": (?P<time_micros>\d+)" \
						", \"cf_name\": \"default\"" \
						", \"job\": (?P<job>\d+)" \
						", \"event\": \"table_file_creation\"" \
						", \"file_number\": (?P<file_number>\d+)" \
						", \"file_size\": (?P<file_size>\d+)" \
						", \"path_id\": (?P<path_id>\d+)" \
						".+" \
						", \"reason\": (?P<reason>\w+)" \
						".*"
						, line)
				if mo is not None:
					_SetTabletCreated(mo)
					continue

				# 2016/12/21-02:15:58.341853 7f702dffb700 EVENT_LOG_v1 {"time_micros":
				# 1482304558341847, "job": 227, "event": "table_file_deletion",
				# "file_number": 1058}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d)" \
						".+ EVENT_LOG_v1 {\"time_micros\": (?P<time_micros>\d+)" \
						", \"job\": \d+" \
						", \"event\": \"table_file_deletion\"" \
						", \"file_number\": (?P<file_number>\d+)" \
						"}" \
						".*"
						, line)
				if mo is not None:
					_SetTabletDeleted(mo)
					continue

				# 2017/01/20-23:03:00.960592 7fc8037fe700 EVENT_LOG_v1 {"time_micros":
				# 1484971380960590, "mutant_trivial_move": {"in_sst": "sst_id=145
				# level=1 path_id=0 temp=20.721", "out_sst_path_id": 0}}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d)" \
						".+ EVENT_LOG_v1 {\"time_micros\": (?P<time_micros>\d+)" \
						", \"mutant_trivial_move\": {" \
						"\"in_sst\": \"" \
						"sst_id=(?P<in_sst_id>\d+)" \
						" level=(?P<in_level>\d+)" \
						" path_id=(?P<in_path_id>\d+)" \
						" temp=(?P<in_temp>(\d|\.)+)" \
						"\", \"out_sst_path_id\": (?P<out_path_id>\d+)}}" \
						".*"
						, line)
				if mo is not None:
					_SetTrivialMove(mo)
					continue

				# You can check out the other events here. All useful ones were covered above.
				#Cons.P(line)
			Cons.ClearLine()
			Cons.P("Processed %d lines" % line_no)

		deleted = 0
		not_deleted = 0
		for sst_id, sl in _sst_lives.iteritems():
			if sl.TsDeleted() is None:
				not_deleted += 1
			else:
				deleted += 1
		Cons.P("Created %d SstLives. %d not-deleted, %d deleted"
				% (len(_sst_lives), not_deleted, deleted))

		# Sst_ids have holes between consequtive numbers, like one every 15.
		# Interesting.
		#sst_id_prev = None
		#for sst_id, sl in _sst_lives.iteritems():
		#	if sst_id_prev is None:
		#		Cons.P(sst_id)
		#	else:
		#		if sst_id != sst_id_prev + 1:
		#			Cons.P("-")
		#		Cons.P(sst_id)
		#	sst_id_prev = sst_id


def _SetTabletCreated(mo):
	# Follow ts. time_micros doesn't agrees with the simulated time when you load
	# an existing DB. interesting.
	#ts0 = int(mo.group("time_micros")) / 1000000.0
	#ts = datetime.datetime.fromtimestamp(ts0)
	# 2017/01/20-23:03:00.960592
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	sst_id = int(mo.group("file_number"))
	size = int(mo.group("file_size"))
	#Cons.P("size=%d" % size)
	path_id = int(mo.group("path_id"))
	job_id = int(mo.group("job"))

	level = None
	if mo.group("reason") == "kFlush":
		level = 0

	global _sst_lives
	if sst_id in _sst_lives:
		raise RuntimeError("Unexpected")
	sl = SstLife(ts, sst_id, size, path_id, level)
	_sst_lives[sst_id] = sl

	global _jobid_sstlives
	if job_id not in _jobid_sstlives:
		_jobid_sstlives[job_id] = []
	_jobid_sstlives[job_id].append(sl)


def _SetTabletAccess(mo):
	global _sst_lives
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	#if mo.group("memt_acc_cnt") is not None:
	#	for mac in mo.group("memt_acc_cnt").split(" "):
	#		t = mac.split(":")
	#		memt_addr = t[0]
	#		cnt = int(t[1])
	#		if memt_addr not in _memt_lives:
	#			raise RuntimeError("Unexpected")
	#		_memt_lives[memt_addr].SetAccessCnt(ts, cnt)

	if mo.group("sst_acc_cnt") is not None:
		for sac in mo.group("sst_acc_cnt").split(" "):
			t = sac.split(":")
			sst_id = int(t[0])
			# Not reliable. It contains -1.
			#level = int(t[1])
			cnt = int(t[2])
			cnt_per_sec = float(t[3])
			temp = float(t[4])
			if sst_id not in _sst_lives:
				raise RuntimeError("Unexpected")
			_sst_lives[sst_id].SetAccessCnt(ts, cnt, cnt_per_sec, temp)


def _SetTabletDeleted(mo):
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	sst_id = int(mo.group("file_number"))

	global _sst_lives
	if sst_id not in _sst_lives:
		# This happens when you load an existing DB. They are all in the hot storage.
		Cons.P("Ignoring deletion of a SSTable that hasn't been created: sst_id=%d" % sst_id)
		#raise RuntimeError("Unexpected: sst_id=%d" % sst_id)
	else:
		_sst_lives[sst_id].SetDeleted(ts)


def _SetTrivialMove(mo):
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	in_sst_id = int(mo.group("in_sst_id"))
	in_level = int(mo.group("in_level"))
	in_path_id = int(mo.group("in_path_id"))
	in_temp  = float(mo.group("in_temp"))
	out_path_id = int(mo.group("out_path_id"))

	if in_path_id != out_path_id:
		raise RuntimeError("Implement!")
		# I don't see any trivial move causing a SSTable to be moved to a colder
		# storage device. Implement it once you see it.  The implementation should
		# be straightforward


class MemtLife:
	def __init__(self):
		self.ts_acccnt = {}
		self.ts_deleted = None

	def SetAccessCnt(self, ts, cnt):
		if ts in self.ts_acccnt:
			raise RuntimeError("Unexpected")
		self.ts_acccnt[ts] = cnt
	
	def SetDeleted(self, ts):
		if self.ts_deleted is not None:
			raise RuntimeError("Unexpected")
		self.ts_deleted = ts


class SstLife:
	def __init__(self, ts, sst_id, size, path_id, level):
		self.sst_id = sst_id
		self.ts_created = ts
		self.ts_deleted = None
		self.size = size
		self.path_id = path_id
		self.level = level

		# {ts: (cnt, cnt_per_sec, temp)}
		self.ts_acccnt = {}

		# [
		#   (age_begin
		#   , age_end
		#   , age_begin_simulated_time
		#   , age_end_simulated_time
		#   , cnt_per_sec (at in the middle of (age_begin_simulated_time, age_end_simulated_time))
		#   , temp (at age_end_simulated_time)
		#   )
		# ]
		self.age_accfreq = None

	def SetAccessCnt(self, ts, cnt, cnt_per_sec, temp):
		if ts in self.ts_acccnt:
			raise RuntimeError("Unexpected")
		self.ts_acccnt[ts] = (cnt, cnt_per_sec, temp)

	def SetLevel(self, l):
		if self.level is not None:
			raise RuntimeError("Unexpected")
		self.level = l

	def SetDeleted(self, ts):
		if self.ts_deleted is not None:
			raise RuntimeError("Unexpected")
		self.ts_deleted = ts

	def TsCreated(self):
		return self.ts_created

	def TsDeleted(self):
		return self.ts_deleted
	
	def __str__(self):
		return pprint.pformat(vars(self))
	
	def __repr__(self):
		return self.__str__()

	def LenTsAcccnt(self):
		return len(self.ts_acccnt)

	def WriteAgeAccfreq(self, fo, fmt):
		self._CalcAgeAccfreq()

		for aaf in self.age_accfreq:
			age_begin = aaf[0]
			age_end = aaf[1]
			age_dur = age_end - age_begin
			age_begin_simulated_time = aaf[2]
			age_end_simulated_time = aaf[3]
			age_dur_simulated_time = age_end_simulated_time - age_begin_simulated_time
			# Access frequency = read_per_sec
			read_per_sec = aaf[4]
			temp = aaf[5]

			fo.write((fmt + "\n") \
					% (age_begin, age_end, age_dur
						, age_begin_simulated_time, age_end_simulated_time, age_dur_simulated_time
						, read_per_sec
						, "-" if temp == -1.0 else ("%7.3f" % temp)
						))

	def AgeAccfreq(self):
		self._CalcAgeAccfreq()
		return self.age_accfreq

	def _CalcAgeAccfreq(self):
		if self.age_accfreq is not None:
			return

		# Temperature drops by 0.99 each time unit.
		# When the time unit is sec, temperature 1 drops to 0.001 in 687.31586483
		# seconds, 11 min 27 secs. Seems a reasonable number.
		#   0.99 ^ n = 0.001
		#   n = 687.31586483
		#temp_drop_alpha = 0.99
		#age_end_simulated_time_prev = None
		#temp = None

		self.age_accfreq = []
		age_end_prev = None
		cnt_per_size_first_5_min = 0.0
		for ts, v in sorted(self.ts_acccnt.iteritems()):
			age_end = (ts - self.ts_created).total_seconds()
			age_begin = age_end - 1.0
			if age_begin < 0.0:
				age_begin = 0.0
			if (age_end_prev is not None) and (age_begin < age_end_prev):
				age_begin = age_end_prev

			# Simulated time
			age_begin_simulated_time = SimTime.ToSimulatedTimeDur(age_begin)
			age_end_simulated_time = SimTime.ToSimulatedTimeDur(age_end)
			# Dur in seconds
			age_dur_simulated_time = age_end_simulated_time - age_begin_simulated_time

			# You don't need this calculation. This was already calculated by
			# RocksDB-Mutant.
			#
			# Unit is num / 64 MB / sec
			# Calculation is as if the accesses are all happened at the time ts
			#cnt_per_size = v[0] / (self.size / (64.0 * 1024 * 1024))
			#acc_freq = cnt_per_size / age_dur_simulated_time
			#
			# Calculate temperature
			# - Defined using simulated time. Let's assume that RocksDB knows the
			#   simulated time. In practice, it's the wall clock time.
			# - Initial temperature: If the first age_begin is less than 10 sec,
			#   consider it as an initial temperature. The 10 sec threshold is in
			#   simulation time, since the reporting granularity, 1 sec, is in
			#   simulation time.
			#
			# Update every 5 minutes or 10. Wait until you actually need it. It's
			# just about plotting. Mutant calculates it in that interval.
			#
			#if age_end_simulated_time < 5*60:
			#	cnt_per_size_first_5_min += cnt_per_size
			#	temp = None
			#else:
			#	if temp is None:
			#		cnt_per_size_first_5_min += cnt_per_size
			#		temp = cnt_per_size_first_5_min / age_end_simulated_time
			#	else:
			#		temp = temp * math.pow(temp_drop_alpha, age_end_simulated_time - age_end_simulated_time_prev) \
			#				+ cnt_per_size * (1.0 - temp_drop_alpha)
			#age_end_simulated_time_prev = age_end_simulated_time

			self.age_accfreq.append((age_begin, age_end
				, age_begin_simulated_time, age_end_simulated_time
				, v[1] # cnt_per_sec
				, v[2] # temp
				))

			age_end_prev = age_end

	
	def Size(self):
		return self.size

	def Level(self):
		return self.level

	def Id(self):
		return self.sst_id

	def PathId(self):
		return self.path_id


#                          $/GB/Month
# Local SSD                0.528
# EBS SSD (gp2)            0.100
# EBS HDD thrp. opt. (st1) 0.045
# EBS HDD cold (sc1)       0.025
_storage_cost = [
		0.528
		, 0.100
		, 0.045
		, 0.025]

# Calculate cost by assuming the EBS SSD is EBS HDD. A quick patch.
#_storage_cost = [
#		0.528
#		, 0.045
#		, 0.045
#		, 0.025]

def _CalcStorageCost():
	global _sst_lives
	if _sst_lives is None:
		raise RuntimeError("Unexpected")

	# Sort them by ts_cd and, to break ties, by sst_id
	# {ts_created_or_deleted: sst_id}
	class TscdSstid:
		def __init__(self, ts, event, sst_id):
			self.ts = ts
			if ts is not None:
				self.ts = SimTime.ToSimulatedTime(self.ts)

			# "C"reated or "D"eleted
			self.event = event
			self.sst_id = sst_id

			if self.ts is not None:
				if SimTime.SimulatedTimeEnd() < self.ts:
					# This happens. Tolerate ts no bigger than SimTime.SimulatedTimeEnd()
					# by 5 minutes, which is small compared with the 14 day time
					# interval.
					if SimTime.SimulatedTimeEnd() < self.ts:
						Cons.P("SimTime.SimulatedTimeEnd() %s < self.ts %s. event=%s. It's okay. Adjust to the former" \
								% (SimTime.SimulatedTimeEnd(), self.ts, event))
						self.ts = SimTime.SimulatedTimeEnd()

			if self.event == "D" and self.ts is None:
				self.ts = SimTime.SimulatedTimeEnd()

			if self.ts is None:
				raise RuntimeError("Unexpected")

		def __str__(self):
			return "(%s %s %d)" % (self.ts, self.event, self.sst_id)

		def __repr__(self):
			return self.__str__()

		@staticmethod
		def Cmp(a, b):
			if a.ts < b.ts:
				return -1
			elif a.ts > b.ts:
				return 1
			else:
				# Breaking tie. The order is not important.
				return (a.sst_id - b.sst_id)
	
	tscd_sstid = []
	for sst_id, sl in _sst_lives.iteritems():
		tscd_sstid.append(TscdSstid(sl.TsCreated(), "C", sst_id))
		tscd_sstid.append(TscdSstid(sl.TsDeleted(), "D", sst_id))
	#Cons.P(pprint.pformat(tscd_sstid))
	
	tscd_sstid = sorted(tscd_sstid, cmp=TscdSstid.Cmp)
	#Cons.P(pprint.pformat(tscd_sstid))

	# Make output dn
	dn = "%s/%s" % (Conf.GetDir("dn_result"), Conf.Get("simulation_time_begin"))
	Util.MkDirs(dn)

	# Calculate current storage size by scanning them from the oldest to the
	# newest. We have 4 storage devices.
	cur_size = [0.0, 0.0, 0.0, 0.0]
	cur_num_ssts = [0, 0, 0, 0]
	# Size * time in byte * sec up to now
	cumulative_size_time = [0.0, 0.0, 0.0, 0.0]
	# Init to simulated_time_begin
	ts_prev = SimTime.SimulatedTimeBegin()
	stat = []

	# Store to a file to that you can plot time vs storage size plot.
	fn = "%s/data-size-by-stg-devs-by-time" % dn
	with open(fn, "w") as fo:
		# 160727-122652.458
		# 12345678901234567
		fmt = "%17s %17s %5d" \
				" %2d %2d %2d %2d" \
				" %2d %2d %2d %2d" \
				" %8.3f %8.3f %8.3f %8.3f %8.3f" \
				" %8.3f %8.3f %8.3f %8.3f %8.3f" \
				" %6.3f %6.3f %6.3f %6.3f %6.3f"
		header = Util.BuildHeader(fmt
				, "ts0 ts1 ts_dur" \
						" prev_num_ssts_0 prev_num_ssts_1 prev_num_ssts_2 prev_num_ssts_3" \
						" cur_num_ssts_0 cur_num_ssts_1 cur_num_ssts_2 cur_num_ssts_3" \
						\
						" prev_size_0_in_MB" \
						" prev_size_1_in_MB" \
						" prev_size_2_in_MB" \
						" prev_size_3_in_MB" \
						" prev_size_sum_in_MB" \
						\
						" cur_size_0_in_MB" \
						" cur_size_1_in_MB" \
						" cur_size_2_in_MB" \
						" cur_size_3_in_MB" \
						" cur_size_sum_in_MB" \
						\
						" cumulative_size_time_0_in_GB*month" \
						" cumulative_size_time_1_in_GB*month" \
						" cumulative_size_time_2_in_GB*month" \
						" cumulative_size_time_3_in_GB*month" \
						" cumulative_size_time_sum_in_GB*month"
						)
		i = 0
		for e in tscd_sstid:
			if i % 40 == 0:
				fo.write("%s\n" % header)
			i += 1

			if e.ts < SimTime.SimulatedTimeBegin():
				Cons.P("e.ts %s < SimTime.SimulatedTimeBegin() %s. Adjusting to the latter. This happens." \
						% (e.ts, SimTime.SimulatedTimeBegin()))
				e.ts = SimTime.SimulatedTimeBegin()

			prev_size = cur_size[:]
			prev_num_ssts = cur_num_ssts[:]

			for j in range(4):
				cumulative_size_time[j] += (cur_size[j] * (e.ts - ts_prev).total_seconds())

			path_id = _sst_lives[e.sst_id].PathId()
			size = _sst_lives[e.sst_id].Size()

			if e.event == "C":
				cur_size[path_id] += size
				cur_num_ssts[path_id] += 1
			elif e.event == "D":
				cur_size[path_id] -= size
				cur_num_ssts[path_id] -= 1
			else:
				raise RuntimeError("Unexpected")

			fo.write((fmt + "\n") % (
				ts_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
				, e.ts.strftime("%y%m%d-%H%M%S.%f")[:-3]
				, (e.ts - ts_prev).total_seconds()

				, prev_num_ssts[0], prev_num_ssts[1], prev_num_ssts[2], prev_num_ssts[3]
				, cur_num_ssts[0], cur_num_ssts[1], cur_num_ssts[2], cur_num_ssts[3]

				, (prev_size[0] / (1024.0 * 1024))
				, (prev_size[1] / (1024.0 * 1024))
				, (prev_size[2] / (1024.0 * 1024))
				, (prev_size[3] / (1024.0 * 1024))
				, (sum(prev_size) / (1024.0 * 1024))
				, (cur_size[0] / (1024.0 * 1024))
				, (cur_size[1] / (1024.0 * 1024))
				, (cur_size[2] / (1024.0 * 1024))
				, (cur_size[3] / (1024.0 * 1024))
				, (sum(cur_size) / (1024.0 * 1024))
				, (cumulative_size_time[0] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12))
				, (cumulative_size_time[1] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12))
				, (cumulative_size_time[2] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12))
				, (cumulative_size_time[3] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12))
				, (sum(cumulative_size_time) / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12))
				))

			ts_prev = e.ts
		# Don't bother with printing the last row. Quite a lot of the last rows
		# have the same timestamps.

		stat.append("Data size-time (GB*Month):")
		stat.append("  Local SSD   : %f" % (cumulative_size_time[0] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS SSD     : %f" % (cumulative_size_time[1] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS Mag     : %f" % (cumulative_size_time[2] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS Mag Cold: %f" % (cumulative_size_time[3] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  Sum         : %f" % (sum(cumulative_size_time) / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))

		stat.append("Storage cost ($):")
		stat.append("  Local SSD   : %f" % (_storage_cost[0] * cumulative_size_time[0] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS SSD     : %f" % (_storage_cost[1] * cumulative_size_time[1] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS Mag     : %f" % (_storage_cost[2] * cumulative_size_time[2] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  EBS Mag Cold: %f" % (_storage_cost[3] * cumulative_size_time[3] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))
		stat.append("  Sum         : %f" % (
			(_storage_cost[0] * cumulative_size_time[0]
				+ _storage_cost[1] * cumulative_size_time[1]
				+ _storage_cost[2] * cumulative_size_time[2]
				+ _storage_cost[3] * cumulative_size_time[3])
			/ (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)))

		for l in stat:
			fo.write("# %s\n" % l)
	Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))

	for l in stat:
		Cons.P(l)

	# The other cost (CPU + memory) is dominated by the storage cost.  Shown in
	# the intro of the paper.
