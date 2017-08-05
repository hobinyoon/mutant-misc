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

import SimTime


class RocksDbLogReader:
	def __init__(self, simulation_time_begin):
		self.simulation_time_begin = simulation_time_begin

		self.sim_time = SimTime.SimTime(simulation_time_begin)

		# {sst_id: SstLife()}
		self.sst_lives = None

		self._BuildSstLives()

		self._CalcStorageCost()


	# Read log and parse events: SSTable creation, deletion, levels (not sure if
	# this is used), how_created (if needed)
	#
	# We don't analyze memtable accesses. RocksDB log has the creation times and
	# number.  Haven't looked at how to log them or relate them with the address.
	def _BuildSstLives(self):
		with Cons.MT("Building sst lives ..."):
			self.sst_lives = {}

			dn = "%s/work/mutant/misc/rocksdb/log/rocksdb" % os.path.expanduser("~")
			fn = "%s/%s" % (dn, self.simulation_time_begin)
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
						self._SetTabletCreated(mo)
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
						self._SetTabletDeleted(mo)
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
						self._SetTrivialMove(mo)
						continue

					# You can check out the other events here. All useful ones were covered above.

				Cons.P("Processed %d lines" % line_no)

			deleted = 0
			not_deleted = 0
			for sst_id, sl in self.sst_lives.iteritems():
				if sl.TsDeleted() is None:
					not_deleted += 1
				else:
					deleted += 1
			Cons.P("Created %d SstLives. %d not-deleted, %d deleted"
					% (len(self.sst_lives), not_deleted, deleted))

			# Sst_ids have holes between consequtive numbers, like one every 15.
			# Interesting.
			#sst_id_prev = None
			#for sst_id, sl in self.sst_lives.iteritems():
			#	if sst_id_prev is None:
			#		Cons.P(sst_id)
			#	else:
			#		if sst_id != sst_id_prev + 1:
			#			Cons.P("-")
			#		Cons.P(sst_id)
			#	sst_id_prev = sst_id


	def _SetTabletCreated(self, mo):
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

		if sst_id in self.sst_lives:
			raise RuntimeError("Unexpected")
		sl = SstLife(ts, sst_id, size, path_id, level)
		self.sst_lives[sst_id] = sl


	def _SetTabletDeleted(self, mo):
		ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")

		sst_id = int(mo.group("file_number"))

		if sst_id not in self.sst_lives:
			# This happens when you load an existing DB. They are all in the hot storage.
			#Cons.P("Ignoring deletion of a SSTable that hasn't been created: sst_id=%d" % sst_id)
			#raise RuntimeError("Unexpected: sst_id=%d" % sst_id)
			pass
		else:
			self.sst_lives[sst_id].SetDeleted(ts)


	def _SetTrivialMove(self, mo):
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


	def _CalcStorageCost(self):
		if self.sst_lives is None:
			raise RuntimeError("Unexpected")

		# Sort them by ts_cd and, to break ties, by sst_id
		# {ts_created_or_deleted: sst_id}
		class TscdSstid:
			def __init__(self, sim_time, ts, event, sst_id):
				self.ts = ts
				if ts is not None:
					self.ts = sim_time.ToSimulatedTime(self.ts)

				# "C"reated or "D"eleted
				self.event = event
				self.sst_id = sst_id

				if self.ts is not None:
					if sim_time.SimulatedTimeEnd() < self.ts:
						# This happens. Tolerate ts no bigger than sim_time.SimulatedTimeEnd()
						# by 5 minutes, which is small compared with the 14 day time
						# interval.
						if (self.ts - sim_time.SimulatedTimeEnd()).total_seconds() > 300:
							raise RuntimeError("Unexpected: sim_time.SimulatedTimeEnd()=%s self.ts=%s" % (sim_time.SimulatedTimeEnd(), self.ts))

				if self.event == "D" and self.ts is None:
					self.ts = sim_time.SimulatedTimeEnd()

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
		for sst_id, sl in self.sst_lives.iteritems():
			tscd_sstid.append(TscdSstid(self.sim_time, sl.TsCreated(), "C", sst_id))
			tscd_sstid.append(TscdSstid(self.sim_time, sl.TsDeleted(), "D", sst_id))
		#Cons.P(pprint.pformat(tscd_sstid))
		
		tscd_sstid = sorted(tscd_sstid, cmp=TscdSstid.Cmp)
		#Cons.P(pprint.pformat(tscd_sstid))

		# Calculate current storage size by scanning them from the oldest to the
		# newest. We have 4 storage devices.
		cur_size = [0.0, 0.0, 0.0, 0.0]
		cur_num_ssts = [0, 0, 0, 0]
		# Size * time in byte * sec up to now
		cumulative_size_time = [0.0, 0.0, 0.0, 0.0]
		# Init to simulated_time_begin
		ts_prev = self.sim_time.SimulatedTimeBegin()

		for e in tscd_sstid:
			if e.ts < self.sim_time.SimulatedTimeBegin():
				if False:
					Cons.P("e.ts %s < self.sim_time.SimulatedTimeBegin() %s. Adjusting to the latter. This happens." \
							% (e.ts, self.sim_time.SimulatedTimeBegin()))
				e.ts = self.sim_time.SimulatedTimeBegin()

			prev_size = cur_size[:]
			prev_num_ssts = cur_num_ssts[:]

			for j in range(4):
				cumulative_size_time[j] += (cur_size[j] * (e.ts - ts_prev).total_seconds())

			path_id = self.sst_lives[e.sst_id].PathId()
			size = self.sst_lives[e.sst_id].Size()

			if e.event == "C":
				cur_size[path_id] += size
				cur_num_ssts[path_id] += 1
			elif e.event == "D":
				cur_size[path_id] -= size
				cur_num_ssts[path_id] -= 1
			else:
				raise RuntimeError("Unexpected")

			ts_prev = e.ts
		# Don't bother with printing the last row. Quite a lot of the last rows
		# have the same timestamps.

		# {stg_dev: size-time(GB*Month)}
		self.storage_sizetime = {}
		self.storage_sizetime["t0"] = cumulative_size_time[0] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_sizetime["t1"] = cumulative_size_time[1] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_sizetime["t2"] = cumulative_size_time[2] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_sizetime["t3"] = cumulative_size_time[3] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_sizetime["sum"] = sum(cumulative_size_time) / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)

		# {stg_dev: cost($)}
		self.storage_cost = {}
		self.storage_cost["t0"] = _storage_cost[0] * cumulative_size_time[0] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_cost["t1"] = _storage_cost[1] * cumulative_size_time[1] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_cost["t2"] = _storage_cost[2] * cumulative_size_time[2] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_cost["t3"] = _storage_cost[3] * cumulative_size_time[3] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)
		self.storage_cost["sum"] =  \
				(_storage_cost[0]  * cumulative_size_time[0]  \
				+ _storage_cost[1] * cumulative_size_time[1]  \
				+ _storage_cost[2] * cumulative_size_time[2]  \
				+ _storage_cost[3] * cumulative_size_time[3]) \
				/ (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)

		# The other cost (CPU + memory) is dominated by the storage cost.  Shown in
		# the intro of the paper.


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
			age_begin_simulated_time = self.sim_time.ToSimulatedTimeDur(age_begin)
			age_end_simulated_time = self.sim_time.ToSimulatedTimeDur(age_end)
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
