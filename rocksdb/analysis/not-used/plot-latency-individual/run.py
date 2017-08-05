#!/usr/bin/env python

import os
import sys

import Conf
import Plot
import SimTime


def main(argv):
	Conf.ParseArgs()

	# Get the simulation/simulated time begin/end by parsing a client log file
	# with the the same simulation time begin
	SimTime.Init()

	Plot.Plot()


if __name__ == "__main__":
	sys.exit(main(sys.argv))
