#!/usr/bin/env python

import multiprocessing
import os
import re
import signal
import sys  
import time

from scapy.all import * 

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser('~'))
import Cons
import Util


def Extract(fn):
	if _stop_requested:
		return

	fn_out = "%s/%s" % (_dn_out, os.path.splitext(os.path.basename(fn))[0])
	Cons.P("Extracing %s %d to %s" % (fn, os.path.getsize(fn), fn_out))

	pattern = re.compile("(?P<op>[sg]et) full-players:(?P<id>\d+)")

	# Check if there's anything other than get or set. doen't look like.
	#pattern = re.compile("^([sg]et) full-players:(?P<id>\d+)")

	with PcapReader(fn) as pr, open(fn_out, "w") as fo: 
		try:
			i = 0
			for p in pr:
				if _stop_requested:
					return
				i += 1
				if i % 10000 == 0:
					sys.stdout.write(".")
					sys.stdout.flush()
					fo.flush()

				bp = bytes(p.payload)

				for m in pattern.finditer(bp):
					fo.write("%s %s %s\n" % (p.time, m.group("op"), m.group("id")))
		except Exception as e:
			sys.stderr.write("Error: %s\n" % format(e))
	
	Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


_dn_out = "%s/data-set-get" % os.path.dirname(__file__)

_stop_requested = False

# Interesting. All processes except the parent process runs this signal handler.
# http://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool
def signal_handler(signal, frame):
	global _stop_requested
	_stop_requested = True


def main(argv):
	signal.signal(signal.SIGINT, signal_handler)

	Util.MkDirs(_dn_out)

	dn_pcap = "/home/jason/ALL_DATA/quizup/quizup/traces"

	fns = []
	for f in os.listdir(dn_pcap):
		if not f.endswith(".pcap"):
			continue 
		fns.append(os.path.join(dn_pcap, f))
	
	Cons.P("%d pcap files found" % len(fns))
	#for fn in fns:
	#	print(fn)

	p = multiprocessing.Pool()
	p.map(Extract, fns)
	if _stop_requested:
		Cons.P("Stop requested")


if __name__ == "__main__":
	sys.exit(main(sys.argv))
