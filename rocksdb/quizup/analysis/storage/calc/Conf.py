import argparse
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons


_args = None

def ParseArgs():
	parser = argparse.ArgumentParser(
			description="Plot SSTables access frequencies and temperatures"
			, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("--simulation_time_begin"
			, type=str

			# mutant_enabled = false
			#, default="170120-233955.139"

			# mutant_enabled = true
			# migration_temperature_threshold = 20
			#, default="170120-225836.143"

			# mutant_enabled = true
			# migration_temperature_threshold = 200
			, default="170121-233010.056"

			# mutant_enabled = true
			# migration_temperature_threshold = 10
			#, default="170204-171900.878"
			# This doesn't have any change in the total SSTable sizes after 22nd
			# around noon. Strange. Redoing the experiment on mjolnir.

			, help="Simulation time begin")

	parser.add_argument("--log_dir"
			, type=str
			, default="~/work/mutant/misc/rocksdb/log"
			, help="Mutant simulation log directory")

	parser.add_argument("--dn_result"
			, type=str
			, default=("%s/../.result" % os.path.dirname(__file__))
			, help="Result directory")
	global _args
	_args = parser.parse_args()

	Cons.P("Parameters:")
	for a in vars(_args):
		Cons.P("%s: %s" % (a, getattr(_args, a)), ind=2)


def Get(k):
	return getattr(_args, k)

def GetDir(k):
	return Get(k).replace("~", os.path.expanduser("~"))
