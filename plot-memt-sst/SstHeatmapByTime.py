import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import HeatColor
import MemtSstLife

# Not sure if I am using heat and temperature correctly. Heat includes the
# mass of an object. I'm using them interchangeably for now.

time_offset_in_sec = 2.0

def Heatmap():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn_hm = "%s/sst-heatmap-by-time-%s" % (Conf.dn_result, Conf.ExpStartTime())
	fn_vl = "%s/sst-heatmap-by-time-vertical-lines-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn_hm) and os.path.isfile(fn_vl):
		return (fn_hm, fn_vl, _MaxHeatFromHeatmapByTimeData(fn_hm))

	sst_lives = MemtSstLife.GetSstLives()

	with Cons.MT("Generating Sst heatmap by time ..."):
		# Gather heat info at n different times
		num_times = Conf.heatmap_by_time_num_times

		if Conf.ExpFinishTime() is None:
			MemtSstLife.SetExpEndTimeFromSstLives()

		min_sst_opened = None
		for sst_gen, sl in sorted(sst_lives.iteritems()):
			min_sst_opened = sl.Opened() if min_sst_opened is None else min(min_sst_opened, sl.Opened())

		# Start time is when the first Sstable is opened, not the experiment start
		# time, when no SSTable exists yet.
		#   Exp start time:          160927-143257.395
		#   First Sstable open time: 160927-143411.273
		#st = datetime.datetime.strptime(Conf.ExpStartTime(), "%y%m%d-%H%M%S.%f")
		st = datetime.datetime.strptime(min_sst_opened, "%y%m%d-%H%M%S.%f")
		et = datetime.datetime.strptime(Conf.ExpFinishTime(),   "%y%m%d-%H%M%S.%f")
		dur = (et - st).total_seconds()

		# { t0: {HeatBoxes} }
		time_heatboxes = {}
		vertical_lines = []
		for i in range(0, num_times):
			t0 = st + datetime.timedelta(seconds=(float(dur) * i / num_times + time_offset_in_sec))
			t1 = st + datetime.timedelta(seconds=(float(dur) * (i+1) / num_times + time_offset_in_sec))
			vertical_lines.append(t1)

			# Heat boxes are sorted by their heat and plotted with the heights
			# proportional to the size.
			boxes = []
			for sst_gen, sl in sorted(sst_lives.iteritems()):
				h = sl.HeatAtTime(t0)
				if h is None:
					continue
				boxes.append(_Box(sl, t0, t1, h))
			boxes.sort(key=lambda b: b.heat, reverse=True)
			time_heatboxes[t0] = boxes

			Cons.ClearLine()
			Cons.Pnnl("%4d/%4d" % (i + 1, num_times))
		print ""
		del vertical_lines[-1]

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

		# Make leftmost time to 0.
		t_first = None
		t_base = datetime.datetime(2000, 1, 1)
		for t, boxes in sorted(time_heatboxes.iteritems()):
			if t_first is None:
				t_first = t
			for b in boxes:
				b.t0 = t_base + (b.t0 - t_first)
				b.t1 = t_base + (b.t1 - t_first)
		for i in range(len(vertical_lines)):
			vertical_lines[i] = t_base + (vertical_lines[i] - t_first)

		fmt = "%4d %1d %17s %17s %6.4f %6.4f" \
				" %8.3f %8d %6s"
		with open(fn_hm, "w") as fo:
			fo.write("# heat_max=%f\n" % MemtSstLife.SstLife.max_heat)

			# y0 is smaller than y1 (y0 is placed higher in the plot than y1).
			fo.write("%s\n" % Util.BuildHeader(fmt, \
					"sst_gen level t0 t1 y0 y1" \
					" heat heat_color heat_color_hex"))

			for t, boxes in sorted(time_heatboxes.iteritems()):
				for b in boxes:
					fo.write((fmt + "\n") % ( \
							b.sl.sst_gen, b.sl.level
							, b.t0.strftime("%y%m%d-%H%M%S.%f")[:-3], b.t1.strftime("%y%m%d-%H%M%S.%f")[:-3]
							, b.y0, b.y1
							, b.heat, b.heat_color, ("%0.6X" % b.heat_color)
							))
				fo.write("\n")
		Cons.P("Created %s %d" % (fn_hm, os.path.getsize(fn_hm)))

		with open(fn_vl, "w") as fo:
			for vl in vertical_lines:
				fo.write("%s\n" % vl.strftime("%y%m%d-%H%M%S.%f")[:-3])
		Cons.P("Created %s %d" % (fn_vl, os.path.getsize(fn_vl)))
	return (fn_hm, fn_vl, MemtSstLife.SstLife.max_heat)


class _Box:
	def __init__(self, sl, t0, t1, heat):
		# SstLife
		self.sl = sl
		self.t0 = t0
		self.t1 = t1
		self.heat = heat
		c = (self.heat / MemtSstLife.SstLife.max_heat)
		self.heat_color = HeatColor.Get(c)
		self.y0 = None
		self.y1 = None


def _MaxHeatFromHeatmapByTimeData(fn):
	with open(fn) as fo:
		for line in fo.readlines():
			if line.startswith("# heat_max="):
				#                 01234567890
				return float(line[11:])
	raise RuntimeError("Unexpected. No heat_max in file %s" % fn)


# TODO: do this for all YCSB workloads
def SstHeatAtLastTime():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn_hlt = "%s/sst-heat-last-time-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn_hlt):
		return fn_hlt

	sst_lives = MemtSstLife.GetSstLives()

	with Cons.MT("Generating Sst heats at the last time ..."):
		# Gather heat info at n different times
		num_times = Conf.heatmap_by_time_num_times

		if Conf.ExpFinishTime() is None:
			MemtSstLife.SetExpEndTimeFromSstLives()

		min_sst_opened = None
		for sst_gen, sl in sorted(sst_lives.iteritems()):
			min_sst_opened = sl.Opened() if min_sst_opened is None else min(min_sst_opened, sl.Opened())

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
			h = sl.HeatAtTime(t)
			if h is None:
				continue
			sstgen_heat.append((sst_gen, h))

		sstgen_heat.sort(key=lambda sh: sh[1], reverse=True)

		# Note: Don't bother with the width proportional to the tablet size for now

		fmt = "%4d %1d %8.3f"
		with open(fn_hlt, "w") as fo:
			# y0 is smaller than y1 (y0 is placed higher in the plot than y1).
			fo.write("%s\n" % Util.BuildHeader(fmt, "sst_gen level heat"))

			for sh in sstgen_heat:
				sst_gen = sh[0]
				heat = sh[1]
				fo.write((fmt + "\n") % (sst_gen, sst_lives[sst_gen].level, heat))
		Cons.P("Created %s %d" % (fn_hlt, os.path.getsize(fn_hlt)))
	return fn_hlt
