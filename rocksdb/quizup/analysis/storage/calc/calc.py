#!/usr/bin/env python

import sys

import Conf
import RocksDbLogReader
import SimTime


def main(argv):
	Conf.ParseArgs()

	SimTime.Init(Conf.Get("simulation_time_begin"))

	RocksDbLogReader.CalcStorageCost()


if __name__ == "__main__":
	sys.exit(main(sys.argv))
