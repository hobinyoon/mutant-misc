import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import CsvFile


def Plot():
	_Cpu()
	_Memory()
	_DiskBps()
	_DiskIops()


def _Cpu():
	with Cons.MT("Plotting cpu ..."):
		env = os.environ.copy()
		env["FN_IN"] = CsvFile.GenDataFileForGnuplot()
		dn = "%s/%s" % (Conf.GetDir("output_dir"), Conf.Get("simulation_time_begin"))
		fn_out = "%s/cpu.pdf" % dn
		env["FN_OUT"] = fn_out
		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/cpu.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def _Memory():
	with Cons.MT("Plotting memory ..."):
		env = os.environ.copy()
		env["FN_IN"] = CsvFile.GenDataFileForGnuplot()
		dn = "%s/%s" % (Conf.GetDir("output_dir"), Conf.Get("simulation_time_begin"))
		fn_out = "%s/memory.pdf" % dn
		env["FN_OUT"] = fn_out
		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/memory.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# TODO: Do I want to translate the numbers to simulated time? Maybe. Figure out
# what would be the best to tell the story.

# TODO: The whole thing needs to be redone so that it generates more read IOs

# So, page cache compression is there.
# http://git.kernel.org/cgit/linux/kernel/git/stable/linux-stable.git/commit/?id=96256460487387d28b8398033928e06eb9e428f7
# What should you do now?
# - Reduce the memory. This should be an easier path.
# - Increase the randomness of the quizup workload generator

def _DiskBps():
	with Cons.MT("Plotting disk B/s ..."):
		env = os.environ.copy()
		env["FN_IN"] = CsvFile.GenDataFileForGnuplot()
		dn = "%s/%s" % (Conf.GetDir("output_dir"), Conf.Get("simulation_time_begin"))
		fn_out = "%s/disk-Bps.pdf" % dn
		env["FN_OUT"] = fn_out
		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/disk-bps.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def _DiskIops():
	with Cons.MT("Plotting disk IO/s ..."):
		env = os.environ.copy()
		env["FN_IN"] = CsvFile.GenDataFileForGnuplot()
		dn = "%s/%s" % (Conf.GetDir("output_dir"), Conf.Get("simulation_time_begin"))
		fn_out = "%s/disk-iops.pdf" % dn
		env["FN_OUT"] = fn_out
		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/disk-iops.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
