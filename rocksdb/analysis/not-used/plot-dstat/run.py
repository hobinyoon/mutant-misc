#!/usr/bin/env python

import os
import pprint
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Plot
import SimTime


# TODO: What story do you want to tell?
# The latency drops once you hit the disk, local SSD or remote disks.
# When the page cache doesn't cache all the sstables, that's when it happens.
# - TODO: Plot latency too
#
# TODO: May want to go slower like 1/2 x, so that the peak CPU usage is like under 60%


def main(argv):
	Conf.ParseArgs()

	# Get the simulation/simulated time begin/end by parsing a client log file
	# with the the same simulation time begin
	SimTime.Init()

	Plot.Plot()


if __name__ == "__main__":
	sys.exit(main(sys.argv))
