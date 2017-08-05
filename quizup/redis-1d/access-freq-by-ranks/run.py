#!/usr/bin/env python

import datetime
import operator
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	Plot()


# Generate a smaller data file
def GetKeyCntData():
	fn_out = "%s/work/quizup/86400-sec-redis-ephemeral-cmds.anonymized.compact.key-accesscnt" \
			% os.path.expanduser("~")
	if os.path.isfile(fn_out):
		return fn_out

	fn_in = "%s/work/quizup/86400-sec-redis-ephemeral-cmds.anonymized.compact.log" \
			% os.path.expanduser("~")
	num_lines = 77836639
	with Cons.MT("Reading %s" % fn_in):
		key_cnt = {}
		with open(fn_in) as fo:
			i = 0
			for line in fo:
				i += 1
				t = line.split()
				for k in t[2:]:
					if k in key_cnt:
						key_cnt[k] += 1
					else:
						key_cnt[k] = 1

				if i % 10000 == 0:
					Cons.ClearLine()
					Cons.Pnnl("%d OPs read (%.2f%%)" % (i, 100.0 * i / num_lines))
				# Useful for testing
				#if i >= 100000:
				#	break
		Cons.ClearLine()
		Cons.P("%d OPs read (%.2f%%)" % (i, 100.0 * i / num_lines))

	with Cons.MT("Writing %s" % fn_out):
		key_cnt_sorted_by_cnt = sorted(key_cnt.items(), key=operator.itemgetter(1), reverse=True)
		with open(fn_out, "w") as fo:
			for kc in key_cnt_sorted_by_cnt:
				fo.write("%s %d\n" % (kc[0], kc[1]))
		Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
		return fn_out


def Plot():
	with Cons.MT("Plotting ..."):
		env = os.environ.copy()

		fn_in = GetKeyCntData()
		env["FN_IN"] = fn_in
		fn_out = "%s.pdf" % fn_in
		env["FN_OUT"] = fn_out

		with Cons.MT("Plotting ..."):
			Util.RunSubp("gnuplot %s/key-access-freq.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
