import math
import os
import pickle
import pprint
import re
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import SstByLevelsWithHeatAtSpecificTimes
import StackedSstWithTempByTime
#import SstInfoByTimeByLevel


def Plot():
	PlotStackedSstWithTempByTime()

	# Too much information to present in the paper
	#if Conf.PlotSstByTimeByLevelsWithHeat():
	#	PlotTabletByTimeByLevelWithHeat()

	# Plot this one first
	#if Conf.PlotSstByLevelsWithHeatAtSpecificTimes():
	#	PlotSstTempAtSpecificTimes()

	#if Conf.PlotSstHeatAtLastTime():
	#	PlotSstHeatAtLastTime()


def PlotTabletByTimeByLevelWithHeat():
	with Cons.MT("Plotting Memtable and SSTables by time by levels with heat ..."):
		env = os.environ.copy()

		# Memtables are not plotted for now
		#env["FN_IN_MEMT"] = GetMemtByTimeData()

		env["FN_IN_SST_INFO"] = SstInfoByTimeByLevel.SstInfo()
		env["FN_IN_SST_LEVEL_INFO"] = SstInfoByTimeByLevel.SstLevelInfo()
		env["FN_IN_SST_HEAT"] = SstInfoByTimeByLevel.SstHeatByTimeByLevel()

		fn_out = "%s/sst-by-time-by-levels-with-heat-%s.pdf" % (Conf.dn_result, Conf.ExpStartTime())
		env["FN_OUT"] = fn_out

		with Cons.MT("Plotting ..."):
			#Util.RunSubp("gnuplot %s/tablet-timeline.gnuplot" % os.path.dirname(__file__), env=env)
			Util.RunSubp("gnuplot %s/sst-by-time-by-levels-with-heat.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotSstTempAtSpecificTimes():
	# At the time m sec after the n-th SSTable is created (time t).  To get the
	# max_plot_height, all plot data files need to be generated before plotting
	# the first one.
	plot_data_fns_at_n = {}
	with Cons.MT("Generating plot data for SSTables by levels with heat at specific times ..."):
		for (n, m) in Conf.times_sst_by_levels_with_heat:
			(fn_in_boxes, fn_in_level_seps) = SstByLevelsWithHeatAtSpecificTimes.Boxes(n, m)
			plot_data_fns_at_n[n] = (fn_in_boxes, fn_in_level_seps)

	with Cons.MT("Plotting SSTables by levels with heat at specific times ..."):
		dn = "%s/sst-by-level-by-ks-range-with-heat" % Conf.dn_result

		for n, (fn_in_boxes, fn_in_level_seps) in sorted(plot_data_fns_at_n.iteritems()):
			env = os.environ.copy()
			env["FN_IN_BOXES"] = fn_in_boxes
			env["FN_IN_LEVEL_INFO"] = fn_in_level_seps
			env["MAX_PLOT_HEIGHT"] = str(SstByLevelsWithHeatAtSpecificTimes.max_plot_height)
			fn_out = "%s/sst-by-level-by-ks-range-with-heat-%s-%s.pdf" % (dn, Conf.ExpStartTime(), n)
			env["FN_OUT"] = fn_out

			Util.RunSubp("gnuplot %s/sst-by-level-by-ks-range-with-heat-at-specific-time.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotStackedSstWithTempByTime():
	# X-axis: time
	# Y-axis: total storage space (depending on the workload, it can grow as time
	# goes by)

	# Sst heatmap boxes by time
	env = os.environ.copy()
	(env["FN_IN_HEATMAP"], env["FN_IN_VERTICAL_LINES"], heat_max) = StackedSstWithTempByTime.GetData()
	fn_out = "%s/stacked-sst-with-temp-by-time-%s.pdf" % (Conf.dn_result, Conf.Get("simulation_time_begin"))
	env["FN_OUT"] = fn_out

	with Cons.MT("Plotting stacked SSTables with temperature by time ..."):
		Util.RunSubp("gnuplot %s/stacked-sst-with-temp-by-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotSstHeatAtLastTime():
	# X-axis: Sstables
	# Y-axis: Heat

	# Sst heatmap boxes by time
	env = os.environ.copy()
	env["FN_IN"] = StackedSstWithTempByTime.SstHeatAtLastTime()
	fn_out = "%s/sst-heat-at-last-time-%s.pdf" % (Conf.dn_result, Conf.ExpStartTime())
	env["FN_OUT"] = fn_out

	with Cons.MT("Plotting SSTable heatmap by time ..."):
		Util.RunSubp("gnuplot %s/sst-heat-at-last-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
