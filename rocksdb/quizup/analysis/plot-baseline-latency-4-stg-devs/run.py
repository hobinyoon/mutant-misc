#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Plot


def main(argv):
	Conf.ParseArgs()

	Util.MkDirs(Conf.GetDir("output_dir"))

	Plot.Plot()


if __name__ == "__main__":
	sys.exit(main(sys.argv))
