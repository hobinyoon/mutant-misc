import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf


def Plot():
	_Read()
	_Write()


def _Read():
	with Cons.MT("Plotting read latency ..."):
		env = os.environ.copy()
		env["FN_IN_LOCAL_SSD"] = _GetLog(Conf.Manifest.Get("Local SSD"))
		env["FN_IN_EBS_GP2"] = _GetLog(Conf.Manifest.Get("EBS gp2"))
		env["FN_IN_EBS_ST1"] = _GetLog(Conf.Manifest.Get("EBS st1"))
		env["FN_IN_EBS_SC1"] = _GetLog(Conf.Manifest.Get("EBS sc1"))
		fn_out = "%s/baseline-time-vs-read-latency-all-stg-devs.pdf" % Conf.GetDir("output_dir")
		env["FN_OUT"] = fn_out
		Util.RunSubp("gnuplot %s/read-latency.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def _Write():
	with Cons.MT("Plotting write latency ..."):
		env = os.environ.copy()
		env["FN_IN_LOCAL_SSD"] = _GetLog(Conf.Manifest.Get("Local SSD"))
		env["FN_IN_EBS_GP2"] = _GetLog(Conf.Manifest.Get("EBS gp2"))
		env["FN_IN_EBS_ST1"] = _GetLog(Conf.Manifest.Get("EBS st1"))
		env["FN_IN_EBS_SC1"] = _GetLog(Conf.Manifest.Get("EBS sc1"))
		fn_out = "%s/baseline-time-vs-write-latency-all-stg-devs.pdf" % Conf.GetDir("output_dir")
		env["FN_OUT"] = fn_out
		Util.RunSubp("gnuplot %s/write-latency.gnuplot" % os.path.dirname(__file__), env=env)
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def _GetLog(dt):
	dn = "%s/client" % Conf.GetDir("log_dir")
	fn = "%s/%s" % (dn, dt)
	if os.path.isfile(fn):
		return fn

	fn_7z = "%s.7z" % fn
	if not os.path.isfile(fn_7z):
		raise RuntimeError("Unexpected")
	Util.RunSubp("cd %s && 7z e %s" % (dn, fn_7z))
	return fn


# Note: Do I want to translate the numbers to simulated time? Maybe. Figure out
# what would be the best to tell the story.
