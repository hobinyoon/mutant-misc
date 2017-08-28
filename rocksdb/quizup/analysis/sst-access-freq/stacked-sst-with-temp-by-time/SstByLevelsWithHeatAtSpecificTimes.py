import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import TempColor
import RocksdbLogReader

box_height = 1.0
y_spacing = 0.5

max_plot_height = None

# TODO: Heat to Temperature. file name.

# SSTables by levels with temperature at specific times. Look at the time m sec after
# the n-th SSTable is created (time t).
def Boxes(n, m):
	# TODO: clean up
	#if Conf.Get("simulation_time_begin") is None:
	#	#MutantLogReader.Get()
	#	RocksdbLogReader.Get()

	dn = "%s/sst-by-level-by-ks-range-with-temperature" % Conf.dn_result
	fn_boxes = "%s/%s-boxes-%d" % (dn, Conf.Get("simulation_time_begin"), n)
	fn_level_info = "%s/%s-level-info-%d" % (dn, Conf.Get("simulation_time_begin"), n)
	if os.path.isfile(fn_boxes) and os.path.isfile(fn_level_info):
		_UpdateMaxPlotHeight(fn_boxes)
		return (fn_boxes, fn_level_info)

	# {sst_id, SstLife()}
	sst_lives = RocksdbLogReader.GetSstLives()

	with Cons.MT("Generating SSTables by level by ks range with temperature at specific time n=%d m=%s ..." % (n, m)):
		Util.MkDirs(dn)

		t0 = sst_lives[n].TsCreated() + datetime.timedelta(seconds=m)

		# May or may not want to use the rectangle height proportional to the
		# SSTable size. We'll see. Log-scale height might be better.
		#
		# Boxes representing SSTables
		boxes = []

		for sst_gen, sl in sorted(sst_lives.iteritems()):
			temp = sl.TempAtTime(t0)
			if temp is None:
				continue
			boxes.append(_Box(sl, temp))

		# Sort boxes by level acendening, sst_gen decending. At the same level, the
		# younger SSTables (with bigger sst_gen number) tend to be hotter.
		boxes.sort(key=lambda b: b.sst_life.Id(), reverse=True)
		boxes.sort(key=lambda b: b.sst_life.Level())

		level_labels_y = [box_height / 2.0]
		level_separators_y = []

		# Set y0 of each box
		cur_y0_max = - (box_height + y_spacing)
		prev_level = None
		for b in boxes:
			if b.sst_life.level == 0:
				b.y0 = cur_y0_max + box_height + y_spacing
				cur_y0_max = b.y0
			else:
				if b.sst_life.level == prev_level:
					b.y0 = cur_y0_max
				else:
					b.y0 = cur_y0_max + box_height + 2*y_spacing
					sep = cur_y0_max + box_height + y_spacing
					level_separators_y.append(sep)
					level_labels_y.append(sep + y_spacing + box_height / 2.0)
					cur_y0_max = b.y0
			prev_level = b.sst_life.level
		global max_plot_height
		max_plot_height = cur_y0_max + box_height + y_spacing if max_plot_height is None \
				else max(max_plot_height, cur_y0_max + box_height + y_spacing)

		fn_boxes = "%s/%s-boxes-%d" % (dn, Conf.Get("simulation_time_begin"), n)
		with open(fn_boxes, "w") as fo:
			fmt = "%3d %1d %9d %6.2f %8d %6s %20d %20d %5.1f"
			fo.write("%s\n" % Util.BuildHeader(fmt, "sst_gen level size temperature(reads_per_sec_per_mb)" \
					" temperature_color temperature_color_hex" \
					" ks_first ks_last box_y0"))
			for b in boxes:
				fo.write((fmt + "\n") % (b.sst_life.Id()
					, b.sst_life.Level()
					, b.sst_life.Size()
					, b.temp
					, b.color, "%0.6X" % b.color
					# This is the problem. RocksDB log doesn't have SSTable keyrange. Oh
					# well. Let's use the Cassandra log and come back.
					, b.sst_life.key_range[0]
					, b.sst_life.key_range[1]
					, b.y0
					))
		Cons.P("Created %s %d" % (fn_boxes, os.path.getsize(fn_boxes)))

		with open(fn_level_info, "w") as fo:
			fmt = "%5s %5s"
			fo.write("%s\n" % Util.BuildHeader(fmt, "level_label_y level_separator_y"))
			for i in range(max(len(level_labels_y), len(level_separators_y))):
				l = "-"
				if i < len(level_labels_y):
					l = "%5.1f" % level_labels_y[i]
				s = "-"
				if i < len(level_separators_y):
					s = "%5.1f" % level_separators_y[i]
				fo.write((fmt + "\n") % (l, s))
		Cons.P("Created %s %d" % (fn_level_info, os.path.getsize(fn_level_info)))

	return (fn_boxes, fn_level_info)


def _UpdateMaxPlotHeight(fn_boxes):
	global max_plot_height
	with open(fn_boxes) as fo:
		for line in fo.readlines():
			if len(line) == 0:
				continue
			if line[0] == "#":
				continue
			line = line.strip()
			if len(line) == 0:
				continue
			tokens = re.split(r" +", line)
			box_y0 = float(tokens[8])
			max_plot_height = (box_y0 + box_height + y_spacing) if max_plot_height is None \
					else max(max_plot_height, box_y0 + box_height + y_spacing)


class _Box:
	def __init__(self, sst_life, temp):
		self.sst_life = sst_life
		self.temp = temp
		c = (self.temp / RocksdbLogReader.SstLife.max_cnt_per_64MB_per_sec)
		self.color = TempColor.Get(c)
		self.y0 = None
