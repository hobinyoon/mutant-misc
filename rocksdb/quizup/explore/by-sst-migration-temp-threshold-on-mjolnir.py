#!/usr/bin/env python

# Run on mjolnir from 0% to 100% to calculate cost

import base64
import math
import os
import signal
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


_stop_requested = False


def sigint_handler(signal, frame):
	global _stop_requested
	_stop_requested = True
	pass


def main(argv):
	signal.signal(signal.SIGINT, sigint_handler)

	if False:
		# [256, 128, ..., 0.25]
		#for i in range(8, -3, -1):
		#
		# [0.125, ..., 0.007812]
		for i in range(-3, -8, -1):
			mig_temp_thrds = math.pow(2, i)
			#Cons.P("mig_temp_thrds=%f" % mig_temp_thrds)
			#continue
			if _stop_requested:
				break
			Util.RunSubp("rm -rf %s/work/rocksdb-data/quizup/*" % os.path.expanduser("~"))
			Util.RunSubp("cd %s/.. && stdbuf -i0 -o0 -e0 ./run.py" \
					" --fast_dev_path=%s/work/rocksdb-data" \
					" --slow_dev1_path=%s/work/rocksdb-data/quizup/t1" \
					" --db_path=%s/work/rocksdb-data/quizup" \
					" --init_db_to_90p_loaded=false" \
					" --evict_cached_data=false" \
					" --memory_limit_in_mb=6144" \
					" --exp_desc=%s" \
					" --monitor_temp=true" \
					" --workload_start_from=-1" \
					" --workload_stop_at=-1" \
					" --simulation_time_dur_in_sec=2000" \
					" --sst_migration_temperature_threshold=%f"
					% (os.path.dirname(__file__)
						, os.path.expanduser("~")
						, os.path.expanduser("~")
						, os.path.expanduser("~")
						, base64.b64encode("Mutant storage by different SSTable migration temperature thresholds")
						, mig_temp_thrds))
	else:
		Util.RunSubp("rm -rf %s/work/rocksdb-data/quizup/*" % os.path.expanduser("~"))
		Util.RunSubp("cd %s/.. && stdbuf -i0 -o0 -e0 ./run.py" \
				" --fast_dev_path=%s/work/rocksdb-data" \
				" --slow_dev1_path=%s/work/rocksdb-data/quizup/t1" \
				" --db_path=%s/work/rocksdb-data/quizup" \
				" --init_db_to_90p_loaded=false" \
				" --evict_cached_data=false" \
				" --memory_limit_in_mb=6144" \
				" --exp_desc=%s" \
				" --cache_filter_index_at_all_levels=false" \
				" --monitor_temp=false" \
				" --migrate_sstables=false" \
				" --workload_start_from=-1" \
				" --workload_stop_at=-1" \
				" --simulation_time_dur_in_sec=2000" \
				" --sst_migration_temperature_threshold=10"
				% (os.path.dirname(__file__)
					, os.path.expanduser("~")
					, os.path.expanduser("~")
					, os.path.expanduser("~")
					, base64.b64encode("Unmodified RocksDB storage usage")
					))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
