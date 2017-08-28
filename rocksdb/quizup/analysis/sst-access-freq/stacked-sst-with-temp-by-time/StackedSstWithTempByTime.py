import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import TempColor
import RocksdbLogReader
import SimTime


time_offset_in_sec = 2.0

def GetData():
	fn_hm = "%s/sst-heatmap-by-time-%s" % (Conf.dn_result, Conf.Get("simulation_time_begin"))
	fn_vl = "%s/sst-heatmap-by-time-vertical-lines-%s" % (Conf.dn_result, Conf.Get("simulation_time_begin"))
	if os.path.isfile(fn_hm) and os.path.isfile(fn_vl):
		return (fn_hm, fn_vl, _MaxHeatFromHeatmapByTimeData(fn_hm))

	# {sst_id, SstLife()}
	sst_lives = RocksdbLogReader.GetSstLives()

	with Cons.MT("Generating Sst heatmap by time ..."):
		# Gather temperature info at n different times
		num_times = Conf.heatmap_by_time_num_times

		# Set start and end times
		# Start time is when the first Sstable is created, not the simulation_time_begin, when no SSTable exists yet.
		#   Exp start time:          160927-143257.395
		#   First Sstable open time: 160927-143411.273
		min_sst_opened = None
		for sst_gen, sl in sorted(sst_lives.iteritems()):
			min_sst_opened = sl.TsCreated() if min_sst_opened is None else min(min_sst_opened, sl.TsCreated())
		st = min_sst_opened
		et = SimTime.SimulationTimeEnd()
		dur = (et - st).total_seconds()

		# { t0: {HeatBoxes} }
		time_heatboxes = {}
		max_temperature = None
		for i in range(0, num_times):
			t0 = st + datetime.timedelta(seconds=(float(dur) * i / num_times + time_offset_in_sec))
			t1 = st + datetime.timedelta(seconds=(float(dur) * (i+1) / num_times + time_offset_in_sec))

			# Sort boxes by their temperature. Heights are proportional to their sizes.
			boxes = []
			for sst_gen, sl in sorted(sst_lives.iteritems()):
				temp = sl.TempAtTime(t0)
				if max_temperature is None:
					max_temperature = temp
				else:
					max_temperature = max(max_temperature, temp)
				if temp is None:
					continue
				boxes.append(_Box(sl, t0, t1, temp))
			boxes.sort(key=lambda b: b.temp, reverse=True)
			time_heatboxes[t0] = boxes

			Cons.ClearLine()
			Cons.Pnnl("%4d/%4d" % (i + 1, num_times))
		print ""

		for t, boxes in sorted(time_heatboxes.iteritems()):
			for b in boxes:
				b.SetTempColor(max_temperature)

		# Set y-coordinate of each box
		for t, boxes in sorted(time_heatboxes.iteritems()):
			total_size = 0
			for b in boxes:
				total_size += b.sl.Size()
			s = 0
			for b in boxes:
				b.y0 = float(s) / total_size
				s += b.sl.Size()
				b.y1 = float(s) / total_size

		# Convert to simulated time
		# { t0: {HeatBoxes} }
		time_heatboxes1 = {}
		for t, boxes in sorted(time_heatboxes.iteritems()):
			t1 = SimTime.ToSimulatedTime(t)
			for b in boxes:
				b.t0 = SimTime.ToSimulatedTime(b.t0)
				b.t1 = SimTime.ToSimulatedTime(b.t1)
			time_heatboxes1[t1] = boxes

		# Make leftmost time to 0.
		t_first = None
		#t_base = datetime.datetime(2000, 1, 1)
		vertical_lines = []
		for t, boxes in sorted(time_heatboxes1.iteritems()):
			if t_first is None:
				t_first = t
			vl = None
			for b in boxes:
				#b.t0 = t_base + (b.t0 - t_first)
				#b.t1 = t_base + (b.t1 - t_first)
				b.t0 = (b.t0 - t_first).total_seconds()
				b.t1 = (b.t1 - t_first).total_seconds()
				vl = b.t1
			vertical_lines.append(vl)
		del vertical_lines[-1]

		fmt = "%4d %1d" \
				" %8d %8d" \
				" %6.4f %6.4f" \
				" %8.3f %11.6f %8d %6s"
		with open(fn_hm, "w") as fo:
			fo.write("# max_temperature=%f\n" % max_temperature)

			# y0 is smaller than y1 (y0 is placed higher in the plot than y1).
			fo.write("%s\n" % Util.BuildHeader(fmt, \
					"sst_gen level t0 t1 y0 y1" \
					" temp temp_relative temp_color heat_color_hex"))

			for t, boxes in sorted(time_heatboxes1.iteritems()):
				for b in boxes:
					fo.write((fmt + "\n") % ( \
							b.sl.Id(), b.sl.Level()
							#, b.t0.strftime("%y%m%d-%H%M%S.%f")[:-3], b.t1.strftime("%y%m%d-%H%M%S.%f")[:-3]
							, b.t0, b.t1
							, b.y0, b.y1
							, b.temp, (float(b.temp) / max_temperature)
							, b.temp_color, ("%0.6X" % b.temp_color)
							))
				fo.write("\n")
		Cons.P("Created %s %d" % (fn_hm, os.path.getsize(fn_hm)))

		with open(fn_vl, "w") as fo:
			for vl in vertical_lines:
				#fo.write("%s\n" % vl.strftime("%y%m%d-%H%M%S.%f")[:-3])
				fo.write("%8d\n" % vl)
		Cons.P("Created %s %d" % (fn_vl, os.path.getsize(fn_vl)))
	return (fn_hm, fn_vl, max_temperature)


class _Box:
	def __init__(self, sl, t0, t1, temp):
		# SstLife
		self.sl = sl
		self.t0 = t0
		self.t1 = t1
		self.temp = temp
		self.y0 = None
		self.y1 = None

	def SetTempColor(self, max_temperature):
		c = self.temp / max_temperature
		self.temp_color = TempColor.Get(c)


def _MaxHeatFromHeatmapByTimeData(fn):
	with open(fn) as fo:
		for line in fo.readlines():
			if line.startswith("# max_temperature="):
				#                 0123456789012345678
				return float(line[18:])
	raise RuntimeError("Unexpected. No heat_max in file %s" % fn)


# TODO: do this for all YCSB workloads
def SstHeatAtLastTime():
	# Set Conf.Get("simulation_time_begin"), if not already set.
	if Conf.Get("simulation_time_begin") is None:
		MutantLogReader.Get()

	fn_hlt = "%s/sst-heat-last-time-%s" % (Conf.dn_result, Conf.Get("simulation_time_begin"))
	if os.path.isfile(fn_hlt):
		return fn_hlt

	sst_lives = MemtSstLife.GetSstLives()

	with Cons.MT("Generating Sst heats at the last time ..."):
		# Gather temperature info at n different times
		num_times = Conf.heatmap_by_time_num_times

		if Conf.ExpFinishTime() is None:
			MemtSstLife.SetExpEndTimeFromSstLives()

		min_sst_opened = None
		for sst_gen, sl in sorted(sst_lives.iteritems()):
			min_sst_opened = sl.TsCreated() if min_sst_opened is None else min(min_sst_opened, sl.TsCreated())

		# Start time is when the first Sstable is opened, not the experiment start
		# time, when no SSTable exists yet.
		#   Exp start time:          160927-143257.395
		#   First Sstable open time: 160927-143411.273
		st = datetime.datetime.strptime(min_sst_opened, "%y%m%d-%H%M%S.%f")
		et = datetime.datetime.strptime(Conf.ExpFinishTime(),   "%y%m%d-%H%M%S.%f")
		dur = (et - st).total_seconds()

		sstgen_heat = []
		t = st + datetime.timedelta(seconds=(float(dur) * (num_times - 1) / num_times + time_offset_in_sec))
		for sst_gen, sl in sorted(sst_lives.iteritems()):
			h = sl.TempAtTime(t)
			if h is None:
				continue
			sstgen_heat.append((sst_gen, h))

		sstgen_heat.sort(key=lambda sh: sh[1], reverse=True)

		# Note: Don't bother with the width proportional to the tablet size for now

		fmt = "%4d %1d %8.3f"
		with open(fn_hlt, "w") as fo:
			# y0 is smaller than y1 (y0 is placed higher in the plot than y1).
			fo.write("%s\n" % Util.BuildHeader(fmt, "sst_gen level temperature"))

			for sh in sstgen_heat:
				sst_gen = sh[0]
				temp = sh[1]
				fo.write((fmt + "\n") % (sst_gen, sst_lives[sst_gen].level, temp))
		Cons.P("Created %s %d" % (fn_hlt, os.path.getsize(fn_hlt)))
	return fn_hlt
