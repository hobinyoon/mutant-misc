#!/usr/bin/env python

import os
import signal
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


_stop_requested = False


def sigint_handler(signal, frame):
	global _stop_requested
	_stop_requested = True
	pass


def main(argv):
	signal.signal(signal.SIGINT, sigint_handler)

	for t in [200, 150, 100, 50, 40, 30, 20, 15, 10, 5, 4, 3, 2, 1]:
		if _stop_requested:
			break
		Util.RunSubp("cd %s/.. && stdbuf -i0 -o0 -e0 ./run.py --sst_migration_temperature_threshold=%d"
				% (os.path.dirname(__file__), t))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
