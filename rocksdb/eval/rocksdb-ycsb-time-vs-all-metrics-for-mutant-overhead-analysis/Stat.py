import math
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def Gen(v0, fn_cdf = None):
  v = list(v0)
  v.sort()
  #Cons.P(v)

  r = Result(v)

  stat = "avg: %12.3f" \
      "\nsd : %12.3f" \
      "\nmin: %12.3f" \
      "\nmax: %12.3f" \
      "\n 1p: %12.3f" \
      "\n25p: %12.3f" \
      "\n50p: %12.3f" \
      "\n75p: %12.3f" \
      "\n90p: %12.3f" \
      "\n99p: %12.3f" \
      "\n99.9p: %12.3f" \
      "\n99.99p: %12.3f" % (
        r.avg, r.sd, r.min, r.max
        , r._1, r._25, r._50, r._75, r._90, r._99, r._999, r._9999
        )
  #Cons.P(stat)

  if fn_cdf is not None:
    with file(fn_cdf, "w") as fo:
      fo.write("%s\n" % Util.Prepend(stat, "# "))
      for i in range(len(v)):
        if (0 < i) and (i < len(v) - 1) and (v[i - 1] == v[i]) and (v[i] == v[i + 1]):
          continue
        fo.write("%s %f\n" % (v[i], float(i) / len(v)))
      fo.write("%s 1.0\n" % v[-1])
    Cons.P("Created %s %d" % (fn_cdf, os.path.getsize(fn_cdf)))

  return r


class Result:
  def __init__(self, v):
    self.min = v[0]
    self.max = v[-1]
    self._1    = v[int(0.01   * (len(v) - 1))]
    self._25   = v[int(0.25   * (len(v) - 1))]
    self._50   = v[int(0.50   * (len(v) - 1))]
    self._75   = v[int(0.75   * (len(v) - 1))]
    self._90   = v[int(0.90   * (len(v) - 1))]
    self._99   = v[int(0.99   * (len(v) - 1))]
    self._999  = v[int(0.999  * (len(v) - 1))]
    self._9999 = v[int(0.9999 * (len(v) - 1))]

    s = 0.0
    s_sq = 0.0
    for e in v:
      s += e
      s_sq += (e * e)
    avg = s / len(v)
    sd = math.sqrt(s_sq / len(v) - (avg * avg))
    self.avg = avg
    self.sd = sd
