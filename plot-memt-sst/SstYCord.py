import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import MemtSstLife


def Calc(sst_lives):
	with Cons.MT("Calculating SSTable Y coords ..."):
		# Do the placement twice to set y_spacing between adjacent blocks.
		y_spacing = 0
		_Calc(sst_lives, y_spacing)

		#max_y_cord = 0
		#for sst_gen, sl in sorted(sst_lives.iteritems()):
		#	max_y_cord = max(max_y_cord, sl.YcordHigh())
		#y_spacing = int(max_y_cord * 0.005)
		#Cons.P("max_y_cord=%d y_spacing=%d" % (max_y_cord, y_spacing))
		#_Calc(sst_lives, y_spacing)


_level_separator_high = None

def _Calc(sst_lives, y_spacing):
	# Space filling by sweeping through the x-axis. Time complexity should be
	# lower than O(n^2) since there will be only a handful of blocks (sstables)
	# going through the sweeping line.

	# Calculate y-coords for each levels
	max_level = 0
	for sst_gen, l in sorted(sst_lives.iteritems()):
		max_level = max(max_level, l.level)
	Cons.P("max_level=%d" % max_level)

	cur_level_base = 0
	global _level_separator_high
	_level_separator_high = {}

	y_spacing_inter_level = y_spacing * 2

	for cur_level in range(max_level + 1):
		# Areas intersecting the current sweep line
		areas = []
		max_y_cord_high = 0

		for sst_gen, sl in sorted(sst_lives.iteritems()):
			if sl.level != cur_level:
				continue

			# Place sl in the plot

			# Delete (not include to new_areas) areas that are past the sweeping line
			new_areas = []
			for a in areas:
				if sl.Opened() <= a.x1:
					new_areas.append(a)
			areas = new_areas

			# Sort areas by the y-coordinates
			areas.sort()

			# Place the current area to the plot while avoiding overlaps with
			# existing areas.
			a0 = Area(sl.Deleted(), 0, sl.Size())
			for a in areas:
				if a.Overlaps(a0, y_spacing):
					a0.Moveup(a.y1 + y_spacing)
			areas.append(a0)
			max_y_cord_high = max(max_y_cord_high, a0.y1)
			sl.SetYcordLow(cur_level_base + a0.y0)

		# The next level starts from one above the current max y_cord_high +
		# y_spacing + inter-level margin (probably like 10 * y_spacing)
		_level_separator_high[cur_level] = cur_level_base + max_y_cord_high + (y_spacing_inter_level / 2.0)
		cur_level_base += (max_y_cord_high + y_spacing_inter_level)


def LevelSepHigh():
	if _level_separator_high is None:
		MemtSstLife.Get()

	return _level_separator_high


class Area:
	def __init__(self, x1, y0, y1):
		# x0, lower bound of x, is not needed
		#
		# x1 can be None, if the tablet is still in use (not deleted yet)
		self.x1 = (Conf.ExpFinishTime() if x1 == None else x1)
		self.y0 = y0
		self.y1 = y1

	def Overlaps(self, other, y_spacing):
		# We only check if the y-ranges overlap. X-ranges don't overlap.
		o_y0 = other.y0 - y_spacing
		o_y1 = other.y1 + y_spacing

		# If self.y0 straddles other's y-range, then overlap.
		if (self.y0 <= o_y0) != (self.y0 <= o_y1):
			return True
		# If self.y1 straddles other's y-range, then overlap.
		if (self.y1 <= o_y0) != (self.y1 <= o_y1):
			return True
		# The same goes with other
		if (o_y0 <= self.y0) != (o_y0 <= self.y1):
			return True
		if (o_y1 <= self.y0) != (o_y1 <= self.y1):
			return True
		return False

	def Moveup(self, y_low):
		height = self.y1 - self.y0
		self.y0 = y_low
		self.y1 = y_low + height

	def __lt__(self, other):
		# Since they don't overlap, we simply compare y0.
		return self.y0 < other.y0
