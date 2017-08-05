import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import CsvFile


def Plot():
	with Cons.MT("Plotting ..."):
		env = os.environ.copy()
		env["FN_IN_LOCAL_SSD"] = CsvFile.GenDataFileForGnuplot(Conf.Manifest.Get("Local SSD"))
		env["FN_IN_EBS_GP2"] = CsvFile.GenDataFileForGnuplot(Conf.Manifest.Get("EBS gp2"))
		env["FN_IN_EBS_ST1"] = CsvFile.GenDataFileForGnuplot(Conf.Manifest.Get("EBS st1"))
		env["FN_IN_EBS_SC1"] = CsvFile.GenDataFileForGnuplot(Conf.Manifest.Get("EBS sc1"))
		fn_out = "%s/baseline-time-vs-resource-usage-all-stg-devs.pdf" % Conf.GetDir("output_dir")
		env["FN_OUT"] = fn_out
		Util.RunSubp("gnuplot %s/res-usage.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# Note: Do I want to translate the numbers to simulated time? Maybe. Figure out
# what would be the best to tell the story.
