#!/usr/bin/env python

import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import DstatLog
from QuizupLog import QuizupLog
import RocksdbLog
import SimTime


def main(argv):
  Conf.ParseArgs()
  Util.MkDirs(Conf.GetDir("output_dir"))

  #job_id = "170829-181631"
  #exp_dt = "170829-221645.216"

  #job_id = "170829-192542"
  #exp_dt = "170830-014718.545"
  #exp_dt = "170830-042708.995"
  #exp_dt = "170830-054649.010"
  #exp_dt = "170830-153428.602"
  #exp_dt = "170830-203631.698"

  #job_id = "170830-163842"
  #exp_dt = "170830-212839.447"

  #job_id = "170830-202118"
  #exp_dt = "170831-005310.542"
  #exp_dt = "170831-011541.748"

  #job_id = "170831-113405"
  #exp_dt = "170831-153420.794"

  #job_id = "170831-110209"
  #exp_dt = "170831-154551.402"

  #job_id = "170831-111144"
  #exp_dt = "170831-155637.210"

  # Makes no sense
  #job_id = "170831-133109"
  #exp_dt = "170831-173125.214"

  #job_id = "170831-140421"
  #exp_dt = "170831-183201.386"

  # Resume from here
  #exp_dt = "170831-190015.298"
  #exp_dt = "170831-191848.134"
  #exp_dt = "170831-193818.890"

  #job_id = "170831-143603"
  #exp_dt = "170831-184202.667"
  #exp_dt = "170831-184334.331"
  #exp_dt = "170831-190944.219"
  #exp_dt = "170831-192627.550"

  # Done
  #job_id = "170831-155754"
  #exp_dt = "170831-195839.169"
  #exp_dt = "170831-200538.279"
  #exp_dt = "170831-200638.899"

  # Useless
  #job_id = "170831-124533"
  #exp_dt = "170831-230308.235"

  #job_id = "170831-192947"
  #exp_dt = "170831-234616.346"
  # Good one
  #exp_dt = "170831-235527.718"
  #exp_dt = "170831-235625.159"

  #job_id = "170902-170944"
  #exp_dt = "170902-214840.754"

  #job_id = "170904-094142"
  #exp_dt = "170904-142142.187"

  job_id = "170904-185540"
  exp_dt = "170904-225625.517"

  dn_log_job = "%s/work/mutant/log/quizup/sla-admin/%s" % (os.path.expanduser("~"), job_id)

  fn_log_quizup  = "%s/quizup/%s" % (dn_log_job, exp_dt)
  fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)
  fn_log_dstat   = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)

  log_q = QuizupLog(fn_log_quizup)
  SimTime.Init(log_q.SimTime("simulated_time_0"), log_q.SimTime("simulated_time_4")
      , log_q.SimTime("simulation_time_0"), log_q.SimTime("simulation_time_4"))

  (fn_rocksdb_sla_admin_log, pid_params) = RocksdbLog.GetSlaAdminLog(fn_log_rocksdb, exp_dt)

  fn_dstat = DstatLog.GenDataFileForGnuplot(fn_log_dstat, exp_dt)

  fn_out = "%s/sla-admin-by-time-%s.pdf" % (Conf.GetDir("output_dir"), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["IN_FN_QZ"] = fn_log_quizup
    env["IN_FN_SLA_ADMIN"] = fn_rocksdb_sla_admin_log
    env["TARGET_LATENCY"] = str(pid_params["target_value"])
    env["PID_PARAMS"] = "%s %s %s" % (pid_params["p"], pid_params["i"], pid_params["d"])
    env["IN_FN_DS"] = fn_dstat
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/sla-admin-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
