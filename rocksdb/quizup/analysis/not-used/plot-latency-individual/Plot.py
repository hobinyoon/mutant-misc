import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


# TODO: Get/put latency in one plot or in 2 separate plots?
# TODO: Put too

def Plot():
	with Cons.MT("Plotting latency ..."):
		env = os.environ.copy()
		env["FN_IN"] = "%s/client/%s" % (Conf.GetDir("log_dir"), Conf.Get("simulation_time_begin"))
		dn = "%s/%s" % (Conf.GetDir("output_dir"), Conf.Get("simulation_time_begin"))
		Util.MkDirs(dn)
		fn_out = "%s/latency.pdf" % dn
		env["FN_OUT"] = fn_out
		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/latency.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# Note: Do I want to translate the numbers to simulated time? Maybe. Figure out
# what would be the best to tell the story.
