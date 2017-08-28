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
	def __init__(self, simulation_time_begin, from_95p = False):
		with Cons.MT("Parsing RocksDB log %s ..." % simulation_time_begin):
			self.simulation_time_begin = simulation_time_begin
			self.sim_time = SimTime.SimTime(simulation_time_begin)
			self.from_95p = from_95p
			if self.from_95p:
				self.simulated_time_95 = self.sim_time.SimulatedTimeBegin() \
						+ datetime.timedelta(seconds = (self.sim_time.SimulatedTimeEnd() - self.sim_time.SimulatedTimeBegin()).total_seconds() * 0.5)
				#Cons.P(self.simulated_time_95)
				# 2016-07-26 17:17:24.123500
			else:
				self.simulated_time_95 = None

			# {sst_id: SstLife()}
			self.sst_lives = None

			self._BuildSstLives()
			self._CalcNumSSTablesSizeAtEachLevelOverTime()


	# Read log and parse events: SSTable creation, deletion, levels, how_created
	# (if needed)
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

			# For setting SSTable levels
			#{ job_id: dest_level }
			self.jobid_destlevel = {}

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

					# These two are to get SSTable levels. From compactions or trivial
					# moves.
					#
					# 2017/02/10-01:05:17.199656 7fa0f17fa700 [default] [JOB 225]
					# Compacting 1@1 + 3@2 files to L2, score 1.01
					mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d)" \
							".+ \[(\w|\d)+\] \[JOB (?P<job_id>\d+)\]" \
							" Compacting \d+@\d+( \+ \d+@\d+)* files" \
							" to L(?P<dest_level>\d), score (\d|\.)+" \
							".*"
							, line)
					if mo is not None:
						self._SetCompacting(mo)
						continue

					# 2017/02/09-20:07:08.521173 7fa0f37fe700 (Original Log Time
					# 2017/02/09-20:07:08.519960) [default] Moving #56 to level-2
					# 67579565 bytes
					mo = re.match(r"(?P<ts>\d\d\d\d/\d\d/\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d)" \
							".+ \[(\w|\d)+\] Moving #(?P<sst_id>\d+) to level-(?P<level>\d) \d+ bytes" \
							".*"
							, line)
					if mo is not None:
						self._SetMoving(mo)
						continue

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
		else:
			if job_id not in self.jobid_destlevel:
				# This happens when you load an existing DB. It's okay.
				Cons.P("sst_id=%d doesn't have a level. It happens in the beginning" % sst_id)
				#raise RuntimeError("Unexpected. sst_id=%d job_id=%d" % (sst_id, job_id))
			else:
				level = self.jobid_destlevel[job_id]

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


	def _SetCompacting(self, mo):
		ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
		job_id = int(mo.group("job_id"))
		if job_id in self.jobid_destlevel:
			raise RuntimeError("Unexpected")
		level = int(mo.group("dest_level"))
		self.jobid_destlevel[job_id] = level


	def _SetMoving(self, mo):
		ts = datetime.datetime.strptime(mo.group("ts"), "%Y/%m/%d-%H:%M:%S.%f")
		sst_id = int(mo.group("sst_id"))
		level = int(mo.group("level"))
		if sst_id not in self.sst_lives:
			raise RuntimeError("Unexpected")
		else:
			self.sst_lives[sst_id].SetLevel(level)


	def _CalcNumSSTablesSizeAtEachLevelOverTime(self):
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

		# Calculate the number of SSTables and size at each level
		cur_num_ssts_by_level = [0, 0, 0]
		cur_size_by_level = [0.0, 0.0, 0.0]
		# Size*time in byte*sec up to now
		cumulative_numssts_time_by_level = [0.0, 0.0, 0.0]
		cumulative_size_time_by_level = [0.0, 0.0, 0.0]

		cur_num_ssts_by_pathid = [0, 0, 0, 0]
		cur_size_by_pathid = [0.0, 0.0, 0.0, 0.0]
		cumulative_numssts_time_by_pathid = [0.0, 0.0, 0.0, 0.0]
		cumulative_size_time_by_pathid = [0.0, 0.0, 0.0, 0.0]

		# Init to simulated_time_begin
		ts_prev = self.sim_time.SimulatedTimeBegin()

		dn = "%s/.output" % os.path.dirname(__file__)
		fn = "%s/num-sstables-size-at-each-level-over-time-%s" % (dn, self.simulation_time_begin)
		with open(fn, "w") as fo:
			# 160727-122652.458
			# 12345678901234567
			fmt = "%17s %17s %5d" \
					" %2d %2d %2d" \
					" %2d %2d %2d" \
					" %8.3f %8.3f %8.3f" \
					" %8.3f %8.3f %8.3f"
			header = Util.BuildHeader(fmt \
					, "ts0 ts1 ts_dur" \
					" prev_num_ssts_L0 prev_num_ssts_L1 prev_num_ssts_L2" \
					" cur_num_ssts_L0 cur_num_ssts_L1 cur_num_ssts_L2" \
					\
					" prev_size_L0_in_MB prev_size_L1_in_MB prev_size_L2_in_MB" \
					" cur_size_L0_in_MB cur_size_L1_in_MB cur_size_L2_in_MB" \
					)

			i = 0
			for e in tscd_sstid:
				if i % 30 == 0:
					fo.write("%s\n" % header)
				i += 1

				if self.simulated_time_95 is None:
					if e.ts < self.sim_time.SimulatedTimeBegin():
						Cons.P("e.ts %s < self.sim_time.SimulatedTimeBegin() %s. Adjusting to the latter. This happens." \
								% (e.ts, self.sim_time.SimulatedTimeBegin()))
						e.ts = self.sim_time.SimulatedTimeBegin()
				else:
					if e.ts < self.simulated_time_95:
						e.ts = self.simulated_time_95

				prev_num_ssts_by_level = cur_num_ssts_by_level[:]
				prev_size_by_level = cur_size_by_level[:]
				prev_num_ssts_by_pathid = cur_num_ssts_by_pathid[:]
				prev_size_by_pathid = cur_size_by_pathid[:]

				for j in range(3):
					cumulative_numssts_time_by_level[j] += (cur_num_ssts_by_level[j] * (e.ts - ts_prev).total_seconds())
					cumulative_size_time_by_level[j] += (cur_size_by_level[j] * (e.ts - ts_prev).total_seconds())
				for j in range(4):
					cumulative_numssts_time_by_pathid[j] += (cur_num_ssts_by_pathid[j] * (e.ts - ts_prev).total_seconds())
					cumulative_size_time_by_pathid[j] += (cur_size_by_pathid[j] * (e.ts - ts_prev).total_seconds())

				level = self.sst_lives[e.sst_id].Level()
				if level is None:
					# Ignore those in the beginning
					if self.simulated_time_95 is None:
						if (e.ts - self.sim_time.SimulatedTimeBegin()).total_seconds() < 1.0:
							ts_prev = e.ts
							continue
					else:
						if e.ts <= self.simulated_time_95:
							ts_prev = e.ts
							continue
					raise RuntimeError("Unexpected: sst_id=%d level is not defined yet. ts_prev=%s ts=%s ts_dur=%d" \
							% (e.sst_id, ts_prev, e.ts, (e.ts - ts_prev).total_seconds()))
				pathid = self.sst_lives[e.sst_id].PathId()
				size = self.sst_lives[e.sst_id].Size()

				if e.event == "C":
					cur_num_ssts_by_level[level] += 1
					cur_size_by_level[level] += size
					cur_num_ssts_by_pathid[pathid] += 1
					cur_size_by_pathid[pathid] += size
				elif e.event == "D":
					cur_num_ssts_by_level[level] -= 1
					cur_size_by_level[level] -= size
					cur_num_ssts_by_pathid[pathid] -= 1
					cur_size_by_pathid[pathid] -= size
				else:
					raise RuntimeError("Unexpected")

				# We'll see if you need by_pathid stat here
				fo.write((fmt + "\n") % (
					ts_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
					, e.ts.strftime("%y%m%d-%H%M%S.%f")[:-3]
					, (e.ts - ts_prev).total_seconds()

					, prev_num_ssts_by_level[0], prev_num_ssts_by_level[1], prev_num_ssts_by_level[2]
					, cur_num_ssts_by_level[0], cur_num_ssts_by_level[1], cur_num_ssts_by_level[2]

					, (prev_size_by_level[0] / (1024.0 * 1024))
					, (prev_size_by_level[1] / (1024.0 * 1024))
					, (prev_size_by_level[2] / (1024.0 * 1024))
					, (cur_size_by_level[0] / (1024.0 * 1024))
					, (cur_size_by_level[1] / (1024.0 * 1024))
					, (cur_size_by_level[2] / (1024.0 * 1024))
					))

				ts_prev = e.ts
			# Don't bother with printing the last row. Quite a lot of the last rows
			# have the same timestamps.

			self.avg_numssts_by_level = {}
			for j in range(3):
				self.avg_numssts_by_level[j] = cumulative_numssts_time_by_level[j] / self.sim_time.SimulatedTimeDur().total_seconds()
			self.avg_sizetime_by_level = {}
			for j in range(3):
				self.avg_sizetime_by_level[j] = cumulative_size_time_by_level[j] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)

			self.avg_numssts_by_pathid = {}
			for j in range(4):
				self.avg_numssts_by_pathid[j] = cumulative_numssts_time_by_pathid[j] / self.sim_time.SimulatedTimeDur().total_seconds()
			self.avg_sizetime_by_pathid = {}
			for j in range(4):
				self.avg_sizetime_by_pathid[j] = cumulative_size_time_by_pathid[j] / (1024.0 * 1024 * 1024) / (3600.0 * 24 * 365.25 / 12)

			stat_str = []
			stat_str.append("Average number of SSTables:")
			for j in range(3):
				stat_str.append("  L%d: %9.6f" % (j, self.avg_numssts_by_level[j]))
			stat_str.append("SSTable size-time (GB*Month):")
			for j in range(3):
				stat_str.append("  L%d: %f" % (j, self.avg_sizetime_by_level[j]))

			for s in stat_str:
				fo.write("# %s\n" % s)
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))


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
