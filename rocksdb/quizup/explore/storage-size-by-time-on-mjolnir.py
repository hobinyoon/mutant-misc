#!/usr/bin/env python

# Run on mjolnir from 0% to 100% to calculate cost

import base64
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Util


def main(argv):
	mig_temp_thrds = 10
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
			" --simulation_time_dur_in_sec=60000" \
			" --sst_migration_temperature_threshold=%f"
			% (os.path.dirname(__file__)
				, os.path.expanduser("~")
				, os.path.expanduser("~")
				, os.path.expanduser("~")
				, base64.b64encode("Mutant storage size over time on mjolnir with SSTable migration temperature threshold 10")
				, mig_temp_thrds))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
