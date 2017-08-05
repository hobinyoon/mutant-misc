#!/usr/bin/env python

import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Plot
import SimTime


def main(argv):
	Conf.ParseArgs()

	SimTime.Init(Conf.Get("simulation_time_begin"))
	Plot.Plot()


if __name__ == "__main__":
	sys.exit(main(sys.argv))
