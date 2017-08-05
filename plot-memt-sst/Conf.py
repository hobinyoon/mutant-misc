import argparse
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons

dn_result = "%s/.result" % os.path.dirname(__file__)

# Mutant option tablet_access_stat_report_interval_in_ms configures this.
mutant_sst_temp_report_interval_in_ms = 500

heat_block_time_granularity_in_sec = 5.0

# SSTables by levels with heat at specific times. Look at the time m sec after
# the n-th SSTable is created (time t).
# - These numbers are hand-picked, specific to experiment 160927-143257.395.
#   You need to load at leat 5000 log lines.
# For the paper
# times_sst_by_levels_with_heat = [
# 		(5, 4)
# 		, (13, 3)
# 		, (22, 4)
# 		, (115, 12)	# Need to load at least 5000 for this
#
# 		# An example where lower level SSTables are hotter than upper level ones.
# 		, (274, 0)	# Don't see 274, but see 275, which is super close to each other.
#
# 		, (299, 1)	# Need to load at least 10000 for this
# 		, (2623, 82)	# Need a fully loaded log
# 		]

# For the poster. 3 is enough for the space. Make sure not to specify more than
# needed. It affect the max level.
times_sst_by_levels_with_heat = [
		(5, 4)
		, (22, 4)
		, (115, 12)
		, (274, 0)	# Don't see 274, but see 275, which is super close to each other.
		]

# 30 makes the 2nd one look kind of cold. It happens, but didn't want to
# distract reviewers.
heatmap_by_time_num_times = 29

_exp_start_time = None
_exp_finish_time = None

_args = None

def ParseArgs():
	parser = argparse.ArgumentParser(
			description="Plot MemTables and SSTables"
			, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("--exp_start_time"
			, type=str

			# workload d
			, default="160927-143257.395"
			#
			# workload a
			#   Use the last dstat datetime
			#, default="161102-155531.196"

			, help="Experiment date time")

	parser.add_argument("--plot_sst_by_time_by_level_with_heat"
			, type=bool
			, default=False
			, help="Plot SSTables by time by levels with heat")
	parser.add_argument("--plot_sst_by_level_with_heat_at_specific_times"
			, type=bool
			, default=False
			, help="Plot SSTables by levels with heat at specific times")
	parser.add_argument("--plot_sst_heatmap_by_time"
			, type=bool
			, default=False
			, help="Plot SSTables heatmap by time")
	parser.add_argument("--plot_sst_heat_at_last_time"
			, type=bool
			, default=False
			, help="Plot SSTables heat at last time")
	parser.add_argument("--max_cass_log_lines"
			, type=int
			, default=10000
			, help="Maximum Cassandra system log lines to load. 0 for unlimited.")
	global _args
	_args = parser.parse_args()

	global _exp_start_time
	_exp_start_time = _args.exp_start_time

	Cons.P("Parameters:")
	for a in vars(_args):
		Cons.P("%s: %s" % (a, getattr(_args, a)), ind=2)

def ExpStartTime():
	return _exp_start_time

def ExpFinishTime():
	return _exp_finish_time

def SetExpStartTime(t):
	global _exp_start_time
	_exp_start_time = t

def SetExpFinishTime(t):
	global _exp_finish_time
	_exp_finish_time = t

def PlotSstByTimeByLevelsWithHeat():
	return _args.plot_sst_by_time_by_level_with_heat

def PlotSstByLevelsWithHeatAtSpecificTimes():
	return _args.plot_sst_by_level_with_heat_at_specific_times

def PlotSstHeatmapByTime():
	return _args.plot_sst_heatmap_by_time

def PlotSstHeatAtLastTime():
	return _args.plot_sst_heat_at_last_time

def MaxCassLogLines():
	return _args.max_cass_log_lines
