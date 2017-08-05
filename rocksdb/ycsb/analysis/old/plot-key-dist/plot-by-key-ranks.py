#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	Plot()


def Plot():
	req_types = ["zipfian", "uniform"]
	for rt in req_types:
		with Cons.MT("Plotting %s ..." % rt):
			fn_in = GetPlotData(rt)
			fn_out = "key-dist-%s-by-rank.pdf" % rt
			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/key-dist-by-rank.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def GetPlotData(req_type):
	fn_in = "data-key-distribution-with-requestdistribution-%s" % req_type
	fn_out = fn_in + "-grouped-by-key-sorted-by-rank"

	if os.path.isfile(fn_out):
		return fn_out

	with Cons.MT("Generating plot data ..."):
		# {key: number_of_occurrences(rank)}
		key_rank = {}

		with open(fn_in) as fo:
			for line in fo.readlines():
				line = line.strip()
				#Cons.P(line)
				k = int(line)
				if k not in key_rank:
					key_rank[k] = 1
				else:
					key_rank[k] += 1

		# [(key, rank)] sorted by rank
		kr_s = []
		for k, r in key_rank.iteritems():
			#Cons.P("%d %d" % (k, r))
			kr_s.append((k, r))

		kr_s.sort(key=lambda a: a[1], reverse=True)

		with open(fn_out, "w") as fo:
			fmt = "%20d %3d"
			fo.write("%s\n" % Util.BuildHeader(fmt, "key rank"))
			for kr in kr_s:
				fo.write((fmt + "\n") % (kr[0], kr[1]))
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
		return fn_out


if __name__ == "__main__":
	sys.exit(main(sys.argv))
