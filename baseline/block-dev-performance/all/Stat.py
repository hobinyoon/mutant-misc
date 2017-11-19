import math
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def GenStat(v0, fn_cdf):
	v = list(v0)
	v.sort()
	#Cons.P(v)

	s = 0.0
	s_sq = 0.0
	for e in v:
		s += e
		s_sq += (e * e)
	avg = s / len(v)
	sd = math.sqrt(s_sq / len(v) - (avg * avg))

	min = v[0]
	max = v[-1]
	_1  = v[int(0.01 * (len(v) - 1))]
	_5  = v[int(0.05 * (len(v) - 1))]
	_10 = v[int(0.10 * (len(v) - 1))]
	_50 = v[int(0.50 * (len(v) - 1))]
	_90 = v[int(0.90 * (len(v) - 1))]
	_95 = v[int(0.95 * (len(v) - 1))]
	_99 = v[int(0.99 * (len(v) - 1))]

	stat = "avg: %7.3f" \
			"\nsd : %7.3f" \
			"\nmin: %7.3f" \
			"\nmax: %7.3f" \
			"\n 1p: %7.3f" \
			"\n 5p: %7.3f" \
			"\n10p: %7.3f" \
			"\n50p: %7.3f" \
			"\n90p: %7.3f" \
			"\n95p: %7.3f" \
			"\n99p: %7.3f" % (
				avg , sd , min , max
				, _1 , _5 , _10 , _50 , _90 , _95 , _99
				)
	Cons.P(stat)

	with file(fn_cdf, "w") as fo:
		fo.write("%s\n" % Util.Prepend(stat, "# "))
		for i in range(len(v)):
			if (0 < i) and (i < len(v) - 1) and (v[i - 1] == v[i]) and (v[i] == v[i + 1]):
				continue
			fo.write("%s %f\n" % (v[i], float(i) / len(v)))
		fo.write("%s 1.0\n" % v[-1])
	Cons.P("Created %s %d" % (fn_cdf, os.path.getsize(fn_cdf)))
