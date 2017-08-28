import os
import yaml


class Manifest:
	_doc = None
	_init = False

	@staticmethod
	def _Init():
		if Manifest._init:
			return
		fn_manifest = "%s/work/mutant/misc/rocksdb/log/manifest.yaml" % os.path.expanduser("~")
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


def StgCost(dev):
	#                          $/GB/Month
	# Local SSD                0.528
	# EBS SSD (gp2)            0.100
	# EBS HDD thrp. opt. (st1) 0.045
	# EBS HDD cold (sc1)       0.025
	storage_cost = {
			"local-ssd1": 0.528
			, "ebs-gp2": 0.100
			, "ebs-st1": 0.045
			, "ebs-sc1": 0.025}
	return storage_cost[dev]
