import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import TempColor
import MemtSstLife
import MutantLogReader
import SstYCord


def SstInfo():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn = "%s/sst-info-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn):
		return fn

	(sst_lives, memt_lives) = MemtSstLife.Get()

	with Cons.MT("Generating Sst info by time by levels data file ..."):
		#with open(fn_m, "w") as fo:
		#	fo.write("%s\n" % Memt.Header())
		#	for addr, l in sorted(_memt_lives.iteritems()):
		#		fo.write("%s\n" % l)
		#Cons.P("Created %s %d" % (fn_m, os.path.getsize(fn_m)))

		with open(fn, "w") as fo:
			fo.write("%s\n" % MemtSstLife.SstLife.Header())
			for sst_gen, l in sorted(sst_lives.iteritems()):
				fo.write("%s\n" % l)
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn


def SstLevelInfo():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn = "%s/sst-info-by-time-by-levels-level-seps-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn):
		return fn

	sst_y_cord_level_sep_highs = SstYCord.LevelSepHigh()

	with Cons.MT("Generating Sst info by time by levels: level separators data file ..."):
		with open(fn, "w") as fo:
			fmt = "%1d %10d %10s"
			fo.write("%s\n" % Util.BuildHeader(fmt
				, "level level_mid_for_labels level_low_for_separators"))
			lh_prev = 0
			for l, lh in sorted(sst_y_cord_level_sep_highs.iteritems()):
				lm = (lh + lh_prev) / 2
				fo.write((fmt + "\n") % (l, lm, lh_prev))
				lh_prev = lh
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn


def SstHeatByTimeByLevel():
	# Set Conf.ExpStartTime(), if not already set.
	if Conf.ExpStartTime() is None:
		MutantLogReader.Get()

	fn = "%s/sst-heat-by-time-by-levels-%s" % (Conf.dn_result, Conf.ExpStartTime())
	if os.path.isfile(fn):
		return fn

	(sst_lives, memt_lives) = MemtSstLife.Get()

	with Cons.MT("Generating SSTable by time by levels with heat data ..."):
		with open(fn, "w") as fo:
			fmt = "%4d %1d %17s %17s %8.1f %13d %13d %8.3f %8d %6s"
			fo.write("%s\n" % Util.BuildHeader(fmt
				, "sst_gen level time0 time1 age_in_sec y0 y1 heat(num_reads_per_sec_per_mb) heat_color heat_color_hex"))

			num_heat_color_blocks_merged = 0
			num_heat_color_blocks = 0

			for sst_gen, sl in sorted(sst_lives.iteritems()):
				# Some SSTables don't have any access stats at all, thus no heat info
				if len(sl.heat_by_time) == 0:
					continue

				t0_begin = None
				t0_prev = None
				t1_prev = None
				heat_prev = None
				heat_color_prev = None

				for t0, v in sl.heat_by_time.items():
					t1 = v[0]
					heat = v[1]

					if t0_begin is None:
						t0_begin = t0

					v = heat / MemtSstLife.SstLife.max_heat
					heat_color = TempColor.Get(v)

					if heat_color == heat_color_prev:
						# No change in t0_prev, heat_color_prev
						t1_prev = t1
						heat_prev = heat
						num_heat_color_blocks_merged += 1
					else:
						if (t0_prev is not None) and (t1_prev is not None) \
								and (heat_prev is not None) \
								and (heat_color_prev is not None):
							fo.write((fmt + "\n") \
									% (sst_gen
										, sst_lives[sst_gen].level
										, t0_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
										, t1_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
										, (t1_prev - t0_begin).total_seconds()
										, sst_lives[sst_gen].y_cord_low, sst_lives[sst_gen].YcordHigh()
										, heat_prev
										, heat_color_prev
										, "%0.6X" % heat_color_prev
										))
							num_heat_color_blocks += 1
						t0_prev = t0
						t1_prev = t1
						heat_prev = heat
						heat_color_prev = heat_color

				# The last one
				if (t0_prev is not None) and (t1_prev is not None) \
						and (heat_prev is not None) \
						and (heat_color_prev is not None):
					fo.write((fmt + "\n") \
							% (sst_gen
								, sst_lives[sst_gen].level
								, t0_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
								, t1_prev.strftime("%y%m%d-%H%M%S.%f")[:-3]
								, (t1_prev - t0_begin).total_seconds()
								, sst_lives[sst_gen].y_cord_low, sst_lives[sst_gen].YcordHigh()
								, heat_prev
								, heat_color_prev
								, "%0.6X" % heat_color_prev
								))
					num_heat_color_blocks += 1

				fo.write("\n")
			Cons.P("num_heat_color_blocks_merged=%d" % num_heat_color_blocks_merged)
			Cons.P("num_heat_color_blocks       =%d" % num_heat_color_blocks)
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
	return fn
