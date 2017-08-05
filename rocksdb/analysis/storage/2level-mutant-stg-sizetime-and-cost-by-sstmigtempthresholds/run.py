#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import StgSizeCost


def main(argv):
	(in_fn, in_fn_individual) = StgSizeCost.GetStgSizeCostData()
	(ur_cost_local_ssd, ur_cost_ebs_ssd, ur_cost_ebs_mag, ur_sizetime) = StgSizeCost.GetUnmodifiedRocksDBSizeCostData()
	out_fn = "%s.pdf" % in_fn

	env = os.environ.copy()
	env["IN_FN"] = in_fn
	#env["IN_FN_INDIVIDUAL"] = in_fn_individual
	env["UR_COST_LOCAL_SSD"] = str(ur_cost_local_ssd)
	env["UR_COST_EBS_SSD"]   = str(ur_cost_ebs_ssd)
	env["UR_COST_EBS_MAG"]   = str(ur_cost_ebs_mag)
	env["UR_SIZETIME"]       = str(ur_sizetime)
	env["OUT_FN"] = out_fn

	with Cons.MT("Plotting ..."):
		Util.RunSubp("gnuplot %s/stg-sizetime-cost-by-sstmigtempthresholds.gnuplot"
				% os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (out_fn, os.path.getsize(out_fn)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
