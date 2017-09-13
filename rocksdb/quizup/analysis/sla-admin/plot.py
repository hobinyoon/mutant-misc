#!/usr/bin/env python

import datetime
import math
import os
import pprint
import re
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

  #job_id = "170904-185540"
  #exp_dt = "170904-225625.517"

  #job_id = "170904-220622"
  #exp_dt = "170905-020747.805"

  #job_id = "170904-221109"
  #exp_dt = "170905-025502.235"

  #job_id = "170904-221143"
  #exp_dt = "170905-024659.084"

  #job_id = "170904-224756"
  #exp_dt = "170905-024816.701"

  #job_id = "170905-010800"
  #exp_dt = "170905-050840.937"
  #job_id = "170905-011221"
  #exp_dt = "170905-051238.471"
  #job_id = "170905-011342"
  #exp_dt = "170905-053208.271"
  #job_id = "170905-011412"
  #exp_dt = "170905-055606.739"

  #job_id = "170905-104927"
  #exp_dt = "170905-144956.585"
  #job_id = "170905-105010"
  #exp_dt = "170905-145026.520"
  #job_id = "170905-105045"
  #exp_dt = "170905-145117.869"
  #job_id = "170905-105155"
  #exp_dt = "170905-145213.241"

  #job_id = "170905-124453"
  #exp_dt = "170905-165025.497"

  # Oscillation. Getting close.
  #job_id = "170905-125629"
  #exp_dt = "170905-165658.468"

  # System was too fast for 30 ms. Should go for lower.
  #job_id = "170905-125742"
  #exp_dt = "170905-165834.321"

  #job_id = "170905-125833"
  #exp_dt = "170905-165900.224"

  #job_id = "170905-174554"
  #exp_dt = "170905-214612.440"
  #job_id = "170905-174713"
  #exp_dt = "170905-214728.224"
  #job_id = "170905-174811"
  #exp_dt = "170905-214822.597"
  #job_id = "170905-174828"
  #exp_dt = "170905-214850.989"

  #job_id = "170905-204638"
  #exp_dt = "170906-004713.465"
  #job_id = "170905-205034"
  #exp_dt = "170906-005101.752"
  #job_id = "170905-205114"
  #exp_dt = "170906-005143.496"
  #job_id = "170905-205137"
  #exp_dt = "170906-005210.092"

  # Full range
  #job_id = "170906-010535"
  #exp_dt = "170906-050616.365"
  #job_id = "170906-010535"
  #exp_dt = "170906-050652.415"
  #job_id = "170906-010535"
  #exp_dt = "170906-050710.117"
  #job_id = "170906-010535"
  #exp_dt = "170906-050724.385"

  # Explore the load
  #job_id = "170906-161010"
  #exp_dt = "170906-205618.503"
  #job_id = "170906-161039"
  #exp_dt = "170906-205659.087"
  #job_id = "170906-161127"
  #exp_dt = "170906-205421.292"
  #job_id = "170906-161155"
  #exp_dt = "170906-205555.173"
  #job_id = "170906-161220"
  #exp_dt = "170906-205627.194"

  # See if you can observe the diurnal latency fluctuations without sla admin
  exps= """170907-012643/quizup/170907-060525.197
    170907-012707/quizup/170907-060630.476
    170907-012728/quizup/170907-060921.104
    170907-012751/quizup/170907-060456.600
    170907-012812/quizup/170907-060408.490
    170907-012834/quizup/170907-060408.086
    170907-012852/quizup/170907-060457.537
    170907-012915/quizup/170907-061430.304
    170907-012937/quizup/170907-060558.257
    170907-012956/quizup/170907-060554.099
    170907-013019/quizup/170907-061145.045
    170907-013041/quizup/170907-060432.527"""

  exps = """170907-121318/quizup/170907-165713.370
    170907-121403/quizup/170907-165712.779
    170907-121440/quizup/170907-165438.591
    170907-121522/quizup/170907-165443.768
    170907-121609/quizup/170907-165218.496
    170907-121653/quizup/170907-165922.539
    170907-121740/quizup/170907-165900.958
    170907-121822/quizup/170907-165822.323
    170907-121904/quizup/170907-170209.779
    170907-122924/quizup/170907-170908.771
    170907-123114/quizup/170907-170943.678
    170907-123205/quizup/170907-171222.564"""

  exps = """170907-123114/quizup/170907-170943.678"""

  exps = """170907-164049/quizup/170907-212518.984
    170907-164110/quizup/170907-211905.715
    170907-164130/quizup/170907-211822.147
    170907-164153/quizup/170907-211909.870
    170907-164222/quizup/170907-213001.374
    170907-164246/quizup/170907-213336.369
    170907-164304/quizup/170907-212518.303
    170907-164326/quizup/170907-220020.817
    170907-164348/quizup/170907-212049.945
    170907-164410/quizup/170907-212045.491
    170907-164429/quizup/170907-212755.838
    170907-164452/quizup/170907-213236.709
    170907-164514/quizup/170907-212552.729
    170907-164536/quizup/170907-213455.280
    170907-164557/quizup/170907-213013.051
    170907-164619/quizup/170907-212735.136
    170907-165226/quizup/170907-212208.496
    170907-235300/quizup/170908-035329.045"""

  exps = """170907-235300/quizup/170908-035329.045"""

  exps = """170908-195136/quizup/170909-003325.826
    170908-200335/quizup/170909-003326.821
    170908-200450/quizup/170909-003330.257
    170908-200648/quizup/170909-003333.434
    170908-200711/quizup/170909-003334.323"""

  # Made a mistake. Oh man.
  #exps = """170909-133452/quizup/170909-181406.862
  #  170909-234250/quizup/170910-034328.419
  #  170909-234319/quizup/170910-034334.963
  #  170909-234341/quizup/170910-034405.061
  #  170909-234355/quizup/170910-034420.568"""

  exps = """170910-125635/quizup/170910-165648.445"""

  exps = """170910-130922/quizup/170910-175350.796
    170910-130946/quizup/170910-175121.624
    170910-131008/quizup/170910-175914.834
    170910-215259/quizup/170911-023919.669
    170910-215323/quizup/170911-023717.417
    170910-215342/quizup/170911-024322.130
    170910-215403/quizup/170911-024013.697"""

  exps = """170911-180901/quizup/170911-225243.953
    170911-191601/quizup/170912-000330.251
    170911-191706/quizup/170912-000344.161
    170911-191727/quizup/170912-001211.393"""

  exps = """170912-090146/quizup/170912-134543.058
    170912-094042/quizup/170912-142410.344"""

  exps = """170912-121125/quizup/170912-165921.714"""

  exps = """170912-090146/quizup/170912-134543.058"""

  exps = """170912-200314/quizup/170913-000846.906
    170912-200725/quizup/170913-000923.763"""

  for line in re.split(r"\s+", exps):
    t = line.split("/quizup/")
    if len(t) != 2:
      raise RuntimeError("Unexpected")
    job_id = t[0]
    exp_dt = t[1]
    Plot(job_id, exp_dt)


def Plot(job_id, exp_dt):
  dn_log_job = "%s/work/mutant/log/quizup/sla-admin/%s" % (os.path.expanduser("~"), job_id)

  fn_log_quizup  = "%s/quizup/%s" % (dn_log_job, exp_dt)
  fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)
  fn_log_dstat   = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)

  log_q = QuizupLog(fn_log_quizup)
  SimTime.Init(log_q.SimTime("simulated_time_0"), log_q.SimTime("simulated_time_4")
      , log_q.SimTime("simulation_time_0"), log_q.SimTime("simulation_time_4"))

  qz_std_max = _QzSimTimeDur(log_q.quizup_options["simulation_time_dur_in_sec"])
  qz_opt_str = _QuizupOptionsFormattedStr(log_q.quizup_options)
  qz_sst_ott_adj_ranges = log_q.quizup_options["sst_ott_adj_ranges"].replace(",", " ")

  (fn_rocksdb_sla_admin_log, pid_params, num_sla_adj, format_version) = RocksdbLog.ParseLog(fn_log_rocksdb, exp_dt)

  fn_dstat = DstatLog.GenDataFileForGnuplot(fn_log_dstat, exp_dt)

  fn_out = "%s/sla-admin-by-time-%s.pdf" % (Conf.GetDir("output_dir"), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["STD_MAX"] = qz_std_max
    env["QZ_SST_OTT_ADJ_RANGES"] = qz_sst_ott_adj_ranges
    env["IN_FN_QZ"] = fn_log_quizup
    env["IN_FN_SLA_ADMIN"] = "" if num_sla_adj == 0 else fn_rocksdb_sla_admin_log
    env["IN_FN_SLA_ADMIN_FORMAT"] = str(format_version)
    env["TARGET_LATENCY"] = str(pid_params["target_value"])
    env["QUIZUP_OPTIONS"] = qz_opt_str
    env["PID_PARAMS"] = "%s %s %s" % (pid_params["p"], pid_params["i"], pid_params["d"])
    env["IN_FN_DS"] = fn_dstat
    env["OUT_FN"] = fn_out
    Util.RunSubp("gnuplot %s/sla-admin-by-time.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


# List the options in 2 columns, column first.
def _QuizupOptionsFormattedStr(quizup_options):
  max_width = 0
  i = 0
  num_rows = int(math.ceil(len(quizup_options) / 2.0))
  for k, v in sorted(quizup_options.iteritems()):
    max_width = max(max_width, len("%s: %s" % (k, v)))
    i += 1
    if i == num_rows:
      break

  strs = []
  fmt = "%%-%ds" % (max_width + 1)
  for k, v in sorted(quizup_options.iteritems()):
    strs.append(fmt % ("%s: %s" % (k, v)))
  #Cons.P("\n".join(strs))
  for i in range(num_rows):
    if i + num_rows < len(strs):
      strs[i] += strs[i + num_rows]
  strs = strs[:num_rows]
  #Cons.P("\n".join(strs))
  qz_opt_str = "\\n".join(strs).replace("_", "\\\\_").replace(" ", "\\ ")
  #Cons.P(qz_opt_str)
  return qz_opt_str


# Simulation time duration
def _QzSimTimeDur(std):
  s = int(std)
  std_s = s % 60
  std_m = int(s / 60) % 60
  std_h = int(s / 3600)
  return "%02d:%02d:%02d" % (std_h, std_m, std_s)


if __name__ == "__main__":
  sys.exit(main(sys.argv))
