#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog
from QuizupLog import QuizupLog
import SimTime


def main(argv):
  Conf.ParseArgs()
  Util.MkDirs(Conf.GetDir("output_dir"))

  job_id = "170829-181631"
  dn_log_job = "%s/work/mutant/log/quizup/sla-admin/%s" % (os.path.expanduser("~"), job_id)
  exp_dt = "170829-221645.216"

  fn_log_quizup  = "%s/quizup/%s" % (dn_log_job, exp_dt)
  fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)
  fn_log_dstat   = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)

  log_q = QuizupLog(fn_log_quizup)
  SimTime.Init(log_q.SimTime("simulated_time_0"), log_q.SimTime("simulated_time_4")
      , log_q.SimTime("simulation_time_0"), log_q.SimTime("simulation_time_4"))

  fn_dstat = DstatLog.GenDataFileForGnuplot(fn_log_dstat, exp_dt)

  fn_out = "%s/sla-admin-by-time-%s.pdf" % (Conf.GetDir("output_dir"), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_FN_QZ"] = fn_log_quizup
    env["IN_FN_DS"] = fn_dstat
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/sla-admin-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
