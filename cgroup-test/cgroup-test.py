#!/usr/bin/env python

import os
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

_dn_test_data = "%s/.test-data" % os.path.dirname(__file__)
_num_files = 10
_file_size = 10 * 1024 * 1024

def main(argv):
	Util.MkDirs(_dn_test_data)
	GenTestData()

	# Evict file cache
	Util.RunSubp("vmtouch -e %s" % _dn_test_data)

	SeqRead()


def GenTestData():
	# Generate _num_files * 100 MB files
	with Cons.MT("Generating test data ..."):
		fn0 = "%s/%02d" %(_dn_test_data, 0)
		if not os.path.isfile(fn0):
			Util.RunSubp("dd if=/dev/urandom of=%s bs=1048576 count=%d" % (fn0, _file_size / 1048576))

		# Generating random data fast
		# - http://serverfault.com/questions/6440/is-there-an-alternative-to-dev-urandom
		for i in range(1, _num_files):
			fn = "%s/%02d" %(_dn_test_data, i)
			if not os.path.isfile(fn):
				Util.RunSubp("openssl enc -aes-256-ctr" \
						" -pass pass:\"$(dd if=/dev/urandom bs=128 count=1 2>/dev/null | base64)\" -nosalt" \
						" < %s > %s" % (fn0, fn))


def SeqRead():
	while True:
		for i in range(_num_files):
			fn = "%s/%02d" %(_dn_test_data, i)
			Cons.Pnnl("Reading %s into memory: " % fn)
			start_time = time.time()
			with open(fn, "rb") as fo:
				data = fo.read(_file_size)
			dur = time.time() - start_time
			print "%3.0f ms" % (dur * 1000.0)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
