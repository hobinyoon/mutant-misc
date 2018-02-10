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


def GetSstAccFreqAtSpecificTime(at_simulated_time):
	fn = "%s/sst-accfreq-%s-at-%.04f" % (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"), at_simulated_time)
	if os.path.isfile(fn):
		return fn

	# t0: a specific time when we take the snapshot
	t0 = SimTime.SimulatedTimeAt(at_simulated_time)
	Cons.P("t0 (time of snapshot): %s" % t0)

	sst_lives = GetSstLives()

	with open(fn, "w") as fo:
		fmt = "%4d %13s %13s %7.3f %1d %5.2f"
		fo.write("# t0 (time of snapshot): %s\n" % t0)
		fo.write("%s\n" % Util.BuildHeader(fmt, "sst_id ts_before ts_after reads_per_64MB_per_sec level age_in_day"))

		for sst_id, sl in sst_lives.iteritems():
			if t0 < SimTime.ToSimulatedTime(sl.ts_created):
				continue
			if (sl.ts_deleted is not None) and (SimTime.ToSimulatedTime(sl.ts_deleted) < t0):
				continue

			ts_prev = None
			for ts, v in sorted(sl.ts_acccnt.iteritems()):
				ts_simulated = SimTime.ToSimulatedTime(ts)
				if ts_simulated < t0:
					ts_prev = ts_simulated
					continue
				#Cons.P("ts_simulated: %s" % ts_simulated)
				if ts_prev is not None:
					#cnt = v[0]
					cnt_per_64MB_per_sec = v[1]
					#temp = v[2]
					fo.write((fmt + "\n") % (sst_id
						, ts_prev.strftime("%y%d%m-%H%M%S")
						, ts_simulated.strftime("%y%d%m-%H%M%S")
						, cnt_per_64MB_per_sec
						, sl.Level()
						, ((t0 - SimTime.ToSimulatedTime(sl.TsCreated())).total_seconds() / 3600.0 / 24)
						))
					break
	Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn


# Read log and parse events: SSTable creation, deletion, accessed, levels,
# how_created (if needed)
#
# We don't analyze memtable accesses. RocksDB log has the creation times and
# number.  Haven't looked at how to log them or relate them with the address.
#_memt_lives = None

# {sst_id, SstLife()}
_sst_lives = None

# For setting the levels.
_jobid_sstlives = {}

def GetSstLives():
	with Cons.MT("Building memt and sst lives ..."):
		#global _memt_lives
		global _sst_lives

		if _sst_lives is not None:
			return _sst_lives

		#_memt_lives = {}
		_sst_lives = {}

		dn = "%s/rocksdb" % Conf.GetDir("rocksdb_log_dir")
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
				if line_no % 100 == 0:
					Cons.ClearLine()
					Cons.Pnnl("Processing line %d" % line_no)

				# The timestamp at the first column and the time_micros are 5 hours
				# apart. One is in local time (EDT) and the other is in UTC. Follow the former.

				# 2016/12/21-02:17:14.329266 7f702d7fa700 EVENT_LOG_v1 {"time_micros":
				# 1482304634329023, "mutant_table_acc_cnt": {"memt":
				# "0x7f69fc00c350:51723 0x7f6bec011200:26942", "sst": "1069:0:30.123:20.123
				# 1059:980:30.123:20.123"}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"mutant_table_acc_cnt\": {(\"memt\": \"(?P<memt_acc_cnt>(\w|\d|:| )+)\")?" \
						"(, )?" \
						"(\"sst\": \"(?P<sst_acc_cnt>(\w|\d|:|-|\.| )+)\")?" \
						"}" \
						".*"
						, line)
				if mo is not None:
					_SetTabletAccess(mo)
					continue

				# 2016/12/21-02:15:58.341853 7f702dffb700 EVENT_LOG_v1 {"time_micros":
				# 1482304558341847, "job": 227, "event": "table_file_deletion",
				# "file_number": 1058}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"job\": \d+" \
						", \"event\": \"table_file_deletion\"" \
						", \"file_number\": (?P<file_number>\d+)" \
						"}" \
						".*"
						, line)
				if mo is not None:
					_SetTabletDeleted(mo)
					continue

				# 2016/12/21-01:27:40.840324 7f702dffb700 EVENT_LOG_v1 {"time_micros":
				# 1482301660840289, "cf_name": "default", "job": 4, "event":
				# "table_file_creation", "file_number": 15, "file_size": 67569420,
				# "table_properties": {"data_size": 67110556, "index_size": 458020,
				# "filter_size": 0, "raw_key_size": 1752468, "raw_average_key_size": 25,
				# "raw_value_size": 65132550, "raw_average_value_size": 966,
				# "num_data_blocks": 16857, "num_entries": 67425, "filter_policy_name":
				# "", "reason": kCompaction, "kDeletedKeys": "0", "kMergeOperands": "0"}}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"cf_name\": \"default\"" \
						", \"job\": (?P<job>\d+)" \
						", \"event\": \"table_file_creation\"" \
						", \"file_number\": (?P<file_number>\d+)" \
						", \"file_size\": (?P<file_size>\d+)" \
						".+" \
						", \"reason\": (?P<reason>\w+)" \
						".*"
						, line)
				if mo is not None:
					_SetTabletCreated(mo)
					continue

				# 2016/12/21-01:28:41.835596 7f683c58d700 EVENT_LOG_v1 {"time_micros":
				# 1482301721835586, "job": 8, "event": "flush_started", "num_memtables":
				# 2, "num_entries": 257306, "num_deletes": 0, "memory_usage": 260052944}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"job\": \d+" \
						", \"event\": \"flush_started\"" \
						".*"
						, line)
				if mo is not None:
					continue

				# 2016/12/21-01:27:25.893816 7f683c58d700 (Original Log Time
				# 2016/12/21-01:27:25.893597) EVENT_LOG_v1 {"time_micros":
				# 1482301645893590, "job": 2, "event": "flush_finished", "lsm_state": [1,
				# 0, 0, 0, 0, 0, 0], "immutable_memtables": 0}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"job\": \d+" \
						", \"event\": \"flush_finished\"" \
						".*"
						, line)
				if mo is not None:
					continue

				# 2016/12/21-01:27:40.010374 7f702dffb700 EVENT_LOG_v1 {"time_micros":
				# 1482301660010345, "job": 4, "event": "compaction_started", "files_L0":
				# [12, 8], "score": 1, "input_data_size": 241744688}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"job\": \d+" \
						", \"event\": \"compaction_started\"" \
						".*"
						, line)
				if mo is not None:
					continue

				# 2016/12/21-01:27:40.960792 7f702dffb700 (Original Log Time
				# 2016/12/21-01:27:40.959919) EVENT_LOG_v1 {"time_micros":
				# 1482301660959908, "job": 4, "event": "compaction_finished",
				# "compaction_time_micros": 949251, "output_level": 1,
				# "num_output_files": 4, "total_output_size": 229662756,
				# "num_input_records": 241171, "num_output_records": 229148,
				# "num_subcompactions": 1, "lsm_state": [0, 4, 0, 0, 0, 0, 0]}
				mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d) .+ EVENT_LOG_v1 {" \
						".+"
						", \"job\": (?P<job>\d+)" \
						", \"event\": \"compaction_finished\"" \
						".+" \
						", \"output_level\": (?P<output_level>\d+)" \
						".*"
						, line)
				if mo is not None:
					_SetCompactinFinished(mo)
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
		return _sst_lives


def _SetTabletAccess(mo):
	global _sst_lives

	# 2016/12/21-02:17:14.329266
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
			cnt_per_64MB_sec = float(t[3])
			temp = float(t[4])
			if sst_id not in _sst_lives:
				raise RuntimeError("Unexpected")
			_sst_lives[sst_id].SetAccessCnt(ts, cnt, cnt_per_64MB_sec, temp)


def _SetTabletCreated(mo):
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	sst_id = int(mo.group("file_number"))
	size = int(mo.group("file_size"))
	job_id = int(mo.group("job"))

	level = None
	if mo.group("reason") == "kFlush":
		level = 0

	global _sst_lives
	if sst_id in _sst_lives:
		raise RuntimeError("Unexpected")
	sl = SstLife(ts, sst_id, size, level)
	_sst_lives[sst_id] = sl

	global _jobid_sstlives
	if job_id not in _jobid_sstlives:
		_jobid_sstlives[job_id] = []
	_jobid_sstlives[job_id].append(sl)


def _SetCompactinFinished(mo):
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	job_id = int(mo.group("job"))
	output_level = int(mo.group("output_level"))

	global _jobid_sstlives
	if job_id not in _jobid_sstlives:
		raise RuntimeError("Unexpected")

	for sl in _jobid_sstlives[job_id]:
		sl.SetLevel(output_level)


def _SetTabletDeleted(mo):
	ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

	sst_id = int(mo.group("file_number"))

	global _sst_lives
	if sst_id not in _sst_lives:
		raise RuntimeError("Unexpected")
	_sst_lives[sst_id].SetDeleted(ts)


#class MemtLife:
#	def __init__(self):
#		self.ts_acccnt = {}
#		self.ts_deleted = None
#
#	def SetAccessCnt(self, ts, cnt):
#		if ts in self.ts_acccnt:
#			raise RuntimeError("Unexpected")
#		self.ts_acccnt[ts] = cnt
#
#	def SetDeleted(self, ts):
#		if self.ts_deleted is not None:
#			raise RuntimeError("Unexpected")
#		self.ts_deleted = ts


class SstLife:
	max_cnt_per_64MB_per_sec = 0

	def __init__(self, ts, sst_id, size, level):
		self.sst_id = sst_id
		self.ts_created = ts
		self.ts_deleted = None
		self.size = size
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

	def SetAccessCnt(self, ts, cnt, cnt_per_64MB_per_sec, temp):
		if ts in self.ts_acccnt:
			raise RuntimeError("Unexpected")

		SstLife.max_cnt_per_64MB_per_sec = max(SstLife.max_cnt_per_64MB_per_sec, cnt_per_64MB_per_sec)
		self.ts_acccnt[ts] = (cnt, cnt_per_64MB_per_sec, temp)

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

			# You don't need to calculate temperature here. It is already calculated by RocksDB-Mutant.

			self.age_accfreq.append((age_begin, age_end
				, age_begin_simulated_time, age_end_simulated_time
				, v[1] # cnt_per_64MB_per_sec
				, v[2] # temp
				))

			age_end_prev = age_end

	def Size(self):
		return self.size

	def Level(self):
		return self.level

	def Id(self):
		return self.sst_id

	# Return approximate heat at time t. You can calculate the exact heat value,
	# but an overkill here. This is just for an illustration.
	def TempAtTime(self, t):
		ts_prev = None
		for ts, v in sorted(self.ts_acccnt.iteritems()):
			if ts < t:
				ts_prev = ts
				continue
			if ts_prev is not None:
				#Cons.P("ts: %s" % ts)
				#cnt = v[0]
				cnt_per_64MB_per_sec = v[1]
				#temp = v[2]
				return cnt_per_64MB_per_sec
		return None
