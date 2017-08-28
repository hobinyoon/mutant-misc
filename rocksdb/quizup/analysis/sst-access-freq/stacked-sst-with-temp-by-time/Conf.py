import argparse
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons

dn_result = "%s/.result" % os.path.dirname(__file__)

# For the poster. 3 is enough for the space. Make sure not to specify more than
# needed. It affect the max level.
#
# Not going for it for now. RocksDB log doesn't have SSTable keyspace ranges.
#times_sst_by_levels_with_heat = [
#		(8, 4)
#		, (22, 4)
#		, (274, 0)	# Don't see 274, but see 275, which is super close to each other.
#		]

heatmap_by_time_num_times = 20

_args = None

def ParseArgs():
	parser = argparse.ArgumentParser(
			description="Plot MemTables and SSTables"
			, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("--simulation_time_begin"
			, type=str
			, default="170213-174445.503"
			, help="Simulation time begin")

	parser.add_argument("--rocksdb_log_dir"
			, type=str
			, default="~/work/mutant/misc/rocksdb/log"
			, help="Mutant RocksDB simulation log directory")

	#parser.add_argument("--plot_sst_by_time_by_level_with_heat"
	#		, type=bool
	#		, default=False
	#		, help="Plot SSTables by time by levels with heat")
	#parser.add_argument("--plot_sst_by_level_with_heat_at_specific_times"
	#		, type=bool
	#		, default=False
	#		, help="Plot SSTables by levels with heat at specific times")
	#parser.add_argument("--plot_sst_heatmap_by_time"
	#		, type=bool
	#		, default=False
	#		, help="Plot SSTables heatmap by time")
	#parser.add_argument("--plot_sst_heat_at_last_time"
	#		, type=bool
	#		, default=False
	#		, help="Plot SSTables heat at last time")
	global _args
	_args = parser.parse_args()

	Cons.P("Parameters:")
	for a in vars(_args):
		Cons.P("%s: %s" % (a, getattr(_args, a)), ind=2)

def Get(k):
	return getattr(_args, k)

def GetDir(k):
	return Get(k).replace("~", os.path.expanduser("~"))
