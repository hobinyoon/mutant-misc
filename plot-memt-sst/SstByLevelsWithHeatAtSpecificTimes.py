import datetime
import math
import os
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import HeatColor
import MemtSstLife

y_spacing = 0.5

max_plot_height = None

# SSTables by levels with heat at specific times. Look at the time m sec after
# the n-th SSTable is created (time t).
def Boxes(n, m):
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	dn = "%s/sst-by-level-by-ks-range-with-heat" % Conf.dn_result
	fn_boxes = "%s/%s-boxes-%d" % (dn, Conf.ExpStartTime(), n)
	fn_level_info = "%s/%s-level-info-%d" % (dn, Conf.ExpStartTime(), n)
	if os.path.isfile(fn_boxes) and os.path.isfile(fn_level_info):
		_UpdateMaxPlotHeight(fn_boxes)
		return (fn_boxes, fn_level_info)

	sst_lives = MemtSstLife.GetSstLives()

	with Cons.MT("Generating SSTables by level by ks range with heat at specific time n=%d m=%s ..." % (n, m)):
		Util.MkDirs(dn)

		t = datetime.datetime.strptime(sst_lives[n].Opened(), "%y%m%d-%H%M%S.%f") \
				+ datetime.timedelta(seconds=m)

		# Boxes representing SSTables
		boxes = []

		for sst_gen, sl in sorted(sst_lives.iteritems()):
			h = sl.HeatAtTime(t)
			if h is None:
				continue
			boxes.append(_Box(sl, h))

		# Sort boxes by level acendening, sst_gen decending. At the same level, the
		# younger SSTables (with bigger sst_gen number) tend to be hotter.
		boxes.sort(key=lambda b: b.sst_life.sst_gen, reverse=True)
		boxes.sort(key=lambda b: b.sst_life.level)

		# Box height: fixed or exponentially growing.
		fixed_box_height = True

		if fixed_box_height:
			box_height = 1
		else:
			box_height = 0.5
		level_labels_y = [box_height / 2.0]
		level_separators_y = []

		# Set y0 of each box
		cur_y0_max = 0
		prev_level = None
		for b in boxes:
			if fixed_box_height:
				box_height = 1
			else:
				box_height = 0.5 * math.pow(2, b.sst_life.level)

			if b.sst_life.level == 0:
				b.y0 = 0
				cur_y0_max = b.y0
			else:
				if b.sst_life.level == prev_level:
					b.y0 = cur_y0_max
				else:
					if fixed_box_height:
						prev_box_height = 1
					else:
						prev_box_height = 0.5 * math.pow(2, prev_level)
					b.y0 = cur_y0_max + prev_box_height + 2*y_spacing
					sep = cur_y0_max + prev_box_height + y_spacing
					level_separators_y.append(sep)
					level_labels_y.append(sep + y_spacing + box_height / 2.0)
					cur_y0_max = b.y0
			b.y1 = b.y0 + box_height
			prev_level = b.sst_life.level
		global max_plot_height
		max_plot_height = cur_y0_max + box_height + y_spacing if max_plot_height is None \
				else max(max_plot_height, cur_y0_max + box_height + y_spacing)

		fn_boxes = "%s/%s-boxes-%d" % (dn, Conf.ExpStartTime(), n)
		with open(fn_boxes, "w") as fo:
			fmt = "%3d %1d %9d %6.2f %8d %6s %20d %20d %5.1f %5.1f"
			fo.write("%s\n" % Util.BuildHeader(fmt, "sst_gen level size heat(reads_per_sec_per_mb)" \
					" heat_color heat_color_hex" \
					" ks_first ks_last box_y0 box_y1"))
			for b in boxes:
				fo.write((fmt + "\n") % (b.sst_life.sst_gen
					, b.sst_life.level
					, b.sst_life.Size()
					, b.heat
					, b.color, "%0.6X" % b.color
					, b.sst_life.key_range[0]
					, b.sst_life.key_range[1]
					, b.y0
					, b.y1
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
			level = int(tokens[1])
			box_y0 = float(tokens[8])
			box_y1 = float(tokens[9])
			max_plot_height = (box_y1 + y_spacing) if max_plot_height is None \
					else max(max_plot_height, box_y1 + y_spacing)


class _Box:
	def __init__(self, sst_life, heat):
		self.sst_life = sst_life
		self.heat = heat
		c = (self.heat / MemtSstLife.SstLife.max_heat)
		self.color = HeatColor.Get(c)
		self.y0 = None
