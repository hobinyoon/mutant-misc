import math
import os
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import RocksDbLogReader
import SimTime


def Plot():
	# Exploring different times to find a good example
	if False:
		for i in range(8000, 10000, 25):
			at_simulated_time = i / 10000.0
			PlotSstAccfreqAtSpecificTime(at_simulated_time)

	PlotSstAccfreqAtSpecificTime(0.9275)

def PlotSstAccfreqAtSpecificTime(at_simulated_time):
	in_fn = RocksDbLogReader.GetSstAccFreqAtSpecificTime(at_simulated_time)
	out_fn = "%s.pdf" % in_fn
	out_fn2 = "%s-2.pdf" % in_fn

	with Cons.MT("Plotting SSTable access frequencies at specific time ..."):
		env = os.environ.copy()
		env["IN_FN"] = in_fn
		env["OUT_FN"] = out_fn
		env["OUT_FN2"] = out_fn2
		Util.RunSubp("gnuplot %s/sst-accfreq-at-specific-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))
		Cons.P("Created %s %d" % (out_fn2, os.path.getsize(out_fn2)))

		# TODO: plot by rank, sst, age, level and (sst or age) and explain why none of them works perfectly.
		# this motivates the needs for direct sstable access monitoring
		# - also, good for guaranteeing latency SLOs, since we are directly working on the access frequencies, rather than indiret metrics.

	return

	with Cons.MT("Plotting SSTable access frequencies at specific time ..."):

		# Plot for all levels. Stop when there is no sstable at a level.
		level = 0
		while True:
			env["LEVEL"] = str(level)
			sst_lives = RocksDbLogReader.GetSstAccFreqByAgeDataFiles(level)
			if len(sst_lives) == 0:
				break
			env["SST_IDS"] = " ".join(str(sl.Id()) for sl in sst_lives)
			env["SST_SIZES"] = " ".join(str(sl.Size()) for sl in sst_lives)

			age_deleted = []
			for sl in sst_lives:
				age_deleted.append(SimTime.ToSimulatedTimeDur((sl.TsDeleted() - sl.TsCreated()).total_seconds()))
			env["AGE_DELETED"] = " ".join(str(i) for i in age_deleted)

			# Age deleted max. Round up with an hour granularity.
			age_deleted_max = max(age_deleted)
			age_deleted_max = math.ceil(age_deleted_max / 3600.0) * 3600
			env["AGE_DELETED_MAX"] = str(age_deleted_max)

			accfreq_max_all_sst_in_level = 0.0
			temp_max_all_sst_in_level = 0.0
			accfreq_max_list = []
			temp_max_list = []
			for sl in sst_lives:
				accfreq_max = 0.0
				temp_max = 0.0
				for accfreq in sl.AgeAccfreq():
					accfreq_max_all_sst_in_level = max(accfreq_max_all_sst_in_level, accfreq[4])
					temp_max_all_sst_in_level = max(temp_max_all_sst_in_level, accfreq[5])
					accfreq_max = max(accfreq_max, accfreq[4])
					temp_max = max(temp_max, accfreq[5])
				accfreq_max_list.append(accfreq_max)
				temp_max_list.append(temp_max)

			Cons.P("Level          : %d" % level)
			Cons.P("Max acc freq   : %f" % max(accfreq_max_list))
			Cons.P("Max temperature: %f" % max(temp_max_list))

			env["ACCFREQ_MAX_ALL_SST_IN LEVEL"] = str(accfreq_max_all_sst_in_level)
			env["TEMP_MAX_ALL_SST_IN_LEVEL"] = str(temp_max_all_sst_in_level)
			env["ACCFREQ_MAX"] = " ".join(str(e) for e in accfreq_max_list)
			env["TEMP_MAX"] = " ".join(str(e) for e in temp_max_list)

			out_fn = "%s/L%d.pdf" % (dn_out, level)
			env["OUT_FN"] = out_fn

			with Cons.MT("Plotting level %d ..." % level):
				Util.RunSubp("gnuplot %s/sst-accfreq-by-age-multiplot-by-level.gnuplot" % os.path.dirname(__file__), env=env, print_cmd=False)
				Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))

			level += 1



def PlotSstAccfreqByAgeIndividualMultiplot():
	with Cons.MT("Plotting individual SSTable access frequencies by their ages ..."):
		dn_out = "%s/%s/sst-age-accfreq-plot" % (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"))
		Util.MkDirs(dn_out)

		env = os.environ.copy()
		dn = "%s/%s/sst-age-accfreq-data" % (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"))
		env["IN_DN"] = dn

		# Plot for all levels. Stop when there is no sstable at a level.
		level = 0
		while True:
			env["LEVEL"] = str(level)
			sst_lives = RocksDbLogReader.GetSstAccFreqByAgeDataFiles(level)
			if len(sst_lives) == 0:
				break
			env["SST_IDS"] = " ".join(str(sl.Id()) for sl in sst_lives)
			env["SST_SIZES"] = " ".join(str(sl.Size()) for sl in sst_lives)

			age_deleted = []
			for sl in sst_lives:
				age_deleted.append(SimTime.ToSimulatedTimeDur((sl.TsDeleted() - sl.TsCreated()).total_seconds()))
			env["AGE_DELETED"] = " ".join(str(i) for i in age_deleted)

			# Age deleted max. Round up with an hour granularity.
			age_deleted_max = max(age_deleted)
			age_deleted_max = math.ceil(age_deleted_max / 3600.0) * 3600
			env["AGE_DELETED_MAX"] = str(age_deleted_max)

			accfreq_max_all_sst_in_level = 0.0
			temp_max_all_sst_in_level = 0.0
			accfreq_max_list = []
			temp_max_list = []
			for sl in sst_lives:
				accfreq_max = 0.0
				temp_max = 0.0
				for accfreq in sl.AgeAccfreq():
					accfreq_max_all_sst_in_level = max(accfreq_max_all_sst_in_level, accfreq[4])
					temp_max_all_sst_in_level = max(temp_max_all_sst_in_level, accfreq[5])
					accfreq_max = max(accfreq_max, accfreq[4])
					temp_max = max(temp_max, accfreq[5])
				accfreq_max_list.append(accfreq_max)
				temp_max_list.append(temp_max)

			Cons.P("Level          : %d" % level)
			Cons.P("Max acc freq   : %f" % max(accfreq_max_list))
			Cons.P("Max temperature: %f" % max(temp_max_list))

			env["ACCFREQ_MAX_ALL_SST_IN LEVEL"] = str(accfreq_max_all_sst_in_level)
			env["TEMP_MAX_ALL_SST_IN_LEVEL"] = str(temp_max_all_sst_in_level)
			env["ACCFREQ_MAX"] = " ".join(str(e) for e in accfreq_max_list)
			env["TEMP_MAX"] = " ".join(str(e) for e in temp_max_list)

			out_fn = "%s/L%d.pdf" % (dn_out, level)
			env["OUT_FN"] = out_fn

			with Cons.MT("Plotting level %d ..." % level):
				Util.RunSubp("gnuplot %s/sst-accfreq-by-age-multiplot-by-level.gnuplot" % os.path.dirname(__file__), env=env, print_cmd=False)
				Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))

			level += 1





def PlotSstAccfreqByAgeAll():
	with Cons.MT("Plotting all SSTable access frequencies by their ages ..."):
		env = os.environ.copy()
		# TODO: Think about grouping once it's done. Like by their starting
		# temperatures or levels.
		#
		# TODO: Think about how to plot Sst ID labels.
		#
		sst_lives = RocksDbLogReader.GetSstAccFreqByAgeDataFiles()
		env["IN_SST_IDS"] = " ".join(str(sl.Id()) for sl in sst_lives)

		dn = "%s/%s/sst-age-accfreq-data" % (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"))
		env["IN_DN"] = dn

		fn_out = "%s/%s/sst-accfreq-by-age-all-%s.pdf" \
				% (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"), Conf.Get("simulation_time_begin"))
		env["OUT_FN"] = fn_out

		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/sst-accfreq-by-age-all.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# Plot all sst lives including the tablet deletion time, individually.
# - Shows the begin and the end time of each time interval with a bar
# - Including the tablet deletion time
def PlotSstAccfreqByAgeIndividual():
	with Cons.MT("Plotting individual SSTable access frequencies by their ages ..."):
		dn_out = "%s/%s/sst-age-accfreq-plot" % (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"))
		Util.MkDirs(dn_out)

		env = os.environ.copy()
		sst_lives = RocksDbLogReader.GetSstAccFreqByAgeDataFiles()
		for sl in sst_lives:
			env["IN_FN"] = "%s/%s/sst-age-accfreq-data/%d" \
					% (Conf.Get("dn_result"), Conf.Get("simulation_time_begin"), sl.Id())
			env["LEVEL"] = str(sl.Level())

			if sl.TsDeleted() is None:
				raise RuntimeError("Unexpected")
			env["AGE_DELETED"] = str(SimTime.ToSimulatedTimeDur((sl.TsDeleted() - sl.TsCreated()).total_seconds()))

			out_fn = "%s/L%d-%d.pdf" % (dn_out, sl.Level(), sl.Id())
			env["OUT_FN"] = out_fn
			start_time = time.time()
			Util.RunSubp("gnuplot %s/sst-accfreq-by-age-individual.gnuplot" % os.path.dirname(__file__), env=env, print_cmd=False)
			dur = time.time() - start_time
			Cons.P("Created %s %d in %.0f ms" % (out_fn, os.path.getsize(out_fn), dur * 1000.0))


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


def PlotSstAccDistAtSpecificTimes():
	# At the time m sec after the n-th SSTable is created (time t).  To get the
	# max_plot_hgieht, all plot data files need to be generated before plotting
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


def PlotSstHeatmapByTime():
	# X-axis: time
	# Y-axis: total storage space (depending on the workload, it can grow as time
	# goes by)

	# Sst heatmap boxes by time
	env = os.environ.copy()
	(env["FN_IN_HEATMAP"], env["FN_IN_VERTICAL_LINES"], heat_max) = SstHeatmapByTime.Heatmap()
	env["HEAT_MAX"] = str(heat_max)
	fn_out = "%s/sst-heatmap-by-time-%s.pdf" % (Conf.dn_result, Conf.ExpStartTime())
	env["FN_OUT"] = fn_out

	with Cons.MT("Plotting SSTable heatmap by time ..."):
		Util.RunSubp("gnuplot %s/sst-heatmap-by-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def PlotSstHeatAtLastTime():
	# X-axis: Sstables
	# Y-axis: Heat

	# Sst heatmap boxes by time
	env = os.environ.copy()
	env["FN_IN"] = SstHeatmapByTime.SstHeatAtLastTime()
	fn_out = "%s/sst-heat-at-last-time-%s.pdf" % (Conf.dn_result, Conf.ExpStartTime())
	env["FN_OUT"] = fn_out

	with Cons.MT("Plotting SSTable heatmap by time ..."):
		Util.RunSubp("gnuplot %s/sst-heat-at-last-time.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
