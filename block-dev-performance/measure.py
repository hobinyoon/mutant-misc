#!/usr/bin/env python

import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

# $ lsblk
# NAME    MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
# xvda    202:0    0     8G  0 disk
# `-xvda1 202:1    0     8G  0 part /
# xvdb    202:16   0    80G  0 disk /mnt/local-ssd0
# xvdc    202:32   0    80G  0 disk /mnt/local-ssd1
# xvdd    202:48   0    80G  0 disk /mnt/ebs-gp2
# xvde    202:64   0   500G  0 disk /mnt/ebs-st1
# xvdf    202:80   0   500G  0 disk /mnt/ebs-sc1

_devs = {"local-ssd": "/mnt/local-ssd0"
		, "ebs-gp2": "/mnt/ebs-gp2"
		, "ebs-st1": "/mnt/ebs-st1"
		, "ebs-sc1": "/mnt/ebs-sc1"}

_dn_result = "%s/result" % os.path.dirname(__file__)

_cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

def main(argv):
	Util.MkDirs(_dn_result)
	GenTestData()
	RandRead()
	SeqWrite({"local-ssd": "/mnt/local-ssd0"})
	SeqWrite(
			{"ebs-gp2": "/mnt/ebs-gp2"
				, "ebs-st1": "/mnt/ebs-st1"
				, "ebs-sc1": "/mnt/ebs-sc1"}
			)
	#FillUpLocalSsd({"local-ssd": "/mnt/local-ssd0"})


def GenTestData():
	with Cons.MT("Generating test data ..."):
		# Generate a big random data file
		if not os.path.isfile("/mnt/local-ssd0/ioping-test-data"):
			Util.RunSubp("sudo dd if=/dev/urandom of=/mnt/local-ssd0/ioping-test-data bs=10240 count=262144")

		for dev_name, dev_dir in _devs.iteritems():
			if dev_name == "local_ssd":
				continue
			fn_test_data = "%s/ioping-test-data" % dev_dir
			if not os.path.isfile(fn_test_data):
				Util.RunSubp("cp /mnt/local-ssd0/ioping-test-data %s/ioping-test-data" % dev_dir)
		Util.RunSubp("sync")


_ioping = "%s/work/ioping/ioping" % os.path.expanduser("~")

def RandRead():
	with Cons.MT("4kb random read test ..."):
		dn_result_ram = "/run/ioping-test-result"
		Util.RunSubp("sudo rm -rf %s" % dn_result_ram)
		Util.RunSubp("sudo mkdir -p %s" % dn_result_ram)
		Util.RunSubp("sudo chown -R ubuntu %s" % dn_result_ram)
		for dev_name, dev_dir in _devs.iteritems():
			fn_log = "%s/4kb-read-%s-%s" % (dn_result_ram, dev_name, _cur_datetime)
			# Request size is 4k by default
			#   -s <size>       request size (4k)
			cmd = "%s -D -c 10000 -i 0 %s/ioping-test-data > %s" % (_ioping, dev_dir, fn_log)
			Util.RunSubp(cmd)
		Cons.P("Copying result to %s" % _dn_result)
		Util.RunSubp("cp %s/* %s/" % (dn_result_ram, _dn_result))
		Util.RunSubp("sync")


def SeqWrite(devs):
	with Cons.MT("128mb sequential write test ..."):
		dn_result_ram = "/run/dd-test-result"
		Util.RunSubp("sudo rm -rf %s" % dn_result_ram)
		Util.RunSubp("sudo mkdir -p %s" % dn_result_ram)
		Util.RunSubp("sudo chown -R ubuntu %s" % dn_result_ram)

		for dev_name, dev_dir in devs.iteritems():
			fn_log = "%s/128mb-seq-write-%s-%s" % (dn_result_ram, dev_name, _cur_datetime)
			for i in range(200):
				cmd = "time -p dd if=/run/ioping-test-data of=%s/dd-test-file-%04d bs=128M count=1 oflag=direct >> %s 2>&1" \
						% (dev_dir, i, fn_log)
				Util.RunSubp(cmd, print_cmd=False)
		Cons.P("Copying result to %s" % _dn_result)
		Util.RunSubp("cp %s/* %s/" % (dn_result_ram, _dn_result))


def FillUpLocalSsd(devs):
	with Cons.MT("128mb sequential write test ..."):
		dn_result_ram = "/run/dd-test-result"
		Util.RunSubp("sudo rm -rf %s" % dn_result_ram)
		Util.RunSubp("sudo mkdir -p %s" % dn_result_ram)
		Util.RunSubp("sudo chown -R ubuntu %s" % dn_result_ram)

		for dev_name, dev_dir in devs.iteritems():
			fn_log = "%s/128mb-seq-write-fill-up-%s-%s" % (dn_result_ram, dev_name, _cur_datetime)
			# 75GB
			for i in range(1000, 2000):
				cmd = "time -p dd if=/run/ioping-test-data of=%s/dd-test-file-%04d bs=246M count=1 oflag=direct >> %s 2>&1" \
						% (dev_dir, i, fn_log)
				Util.RunSubp(cmd, print_cmd=False)
		Cons.P("Copying result to %s" % _dn_result)
		Util.RunSubp("cp %s/* %s/" % (dn_result_ram, _dn_result))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
