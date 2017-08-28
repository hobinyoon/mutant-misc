#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

# Unmodified RocksDB with Local SSD: "170120-233955.139"

#mutant_simulation_time_begin=   "170122-064555.942"  # sstable_migration_temperature_threshold 1
#mutant_simulation_time_begin=   "170122-035822.117"  # sstable_migration_temperature_threshold 10

# Strange. No change in the total SSTable size after 22nd around 12pm
#mutant_simulation_time_begin=   "170204-171900.878"  # sstable_migration_temperature_threshold 10

#mutant_simulation_time_begin=   "170122-025119.060"  # sstable_migration_temperature_threshold 20
#mutant_simulation_time_begin=   "170122-003715.536"  # sstable_migration_temperature_threshold 100
#mutant_simulation_time_begin=   "170121-233010.056"  # sstable_migration_temperature_threshold 200

mutant_simulation_time_begin=   "170207-105022.372" # on mjolnir. perfect.

simulated_time_begin="160711-170502.871"
simulated_time_end=  "160727-122652.458"

def main(argv):
	in_fn_mutant = "%s/../.result/%s/data-size-by-stg-devs-by-time" % (os.path.dirname(__file__), mutant_simulation_time_begin)

	if not os.path.exists(in_fn_mutant):
		Util.RunSubp("%s/../calc/calc.py --simulation_time_begin=%s" % (os.path.dirname(__file__), mutant_simulation_time_begin))

	out_fn = "%s/../.result/mutant-storage-size-by-time-%s.pdf" % (os.path.dirname(__file__), mutant_simulation_time_begin)

	with Cons.MT("Plotting storage size by time ..."):
		env = os.environ.copy()
		env["IN_FN_M"] = in_fn_mutant
		env["OUT_FN"] = out_fn

		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/storage-size-by-time.gnuplot"
					% os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
