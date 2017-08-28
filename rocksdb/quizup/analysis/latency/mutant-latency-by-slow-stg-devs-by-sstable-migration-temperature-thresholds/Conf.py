import argparse
import os
import sys
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons


_args = None

def ParseArgs():
	parser = argparse.ArgumentParser(
			description="Plot system resource usage"
			, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("--log_dir"
			, type=str
			, default="~/work/mutant/misc/rocksdb/log"
			, help="Mutant simulation log directory")

	parser.add_argument("--output_dir"
			, type=str
			, default=("%s/.output" % os.path.dirname(__file__))
			, help="Output directory")
	global _args
	_args = parser.parse_args()

	Cons.P("Parameters:")
	for a in vars(_args):
		Cons.P("%s: %s" % (a, getattr(_args, a)), ind=2)


def Get(k):
	return getattr(_args, k)

def GetDir(k):
	return Get(k).replace("~", os.path.expanduser("~"))


# This class needs to be called after the ParseArgs() above.
class Manifest:
	_doc = None
	_init = False

	@staticmethod
	def _Init():
		if Manifest._init:
			return
		fn_manifest = "%s/manifest.yaml" % GetDir("log_dir")
		with open(fn_manifest, "r") as f:
			Manifest._doc = yaml.load(f)
		Manifest._init = True

	@staticmethod
	def Get(k):
		Manifest._Init()
		return Manifest._doc[k]

	@staticmethod
	def GetDir(k):
		Manifest._Init()
		return Manifest._doc[k].replace("~", os.path.expanduser("~"))
