#!/usr/bin/env python

import datetime
import math
import multiprocessing
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

  exps = """170912-235306/quizup/170913-035333.657
    170912-235306/quizup/170913-055415.634
    170912-235306/quizup/170913-075445.589
    170912-235306/quizup/170913-095515.845
    170912-235806/quizup/170913-035835.113
    170912-235806/quizup/170913-055909.611
    170912-235806/quizup/170913-075944.519
    170912-235806/quizup/170913-100015.814
    170912-235306/quizup/170913-115546.705
    170912-235806/quizup/170913-120051.923"""

  # Figuring out st1 read IO range that has a good impact to latency.
  exps = """170914-000708/quizup/170914-040724.461
    170914-000708/quizup/170914-040728.503
    170914-000708/quizup/170914-060743.656
    170914-000708/quizup/170914-060747.543
    170914-000708/quizup/170914-080805.656
    170914-000708/quizup/170914-080806.895
    170914-000708/quizup/170914-100826.473
    170914-000708/quizup/170914-100828.200
    170914-000708/quizup/170914-120845.944
    170914-000708/quizup/170914-120850.303"""
  #exps = """170914-000708/quizup/170914-080806.895"""

  exps = """170914-150736/quizup/170914-190749.869
    170914-151351/quizup/170914-191411.718
    170914-153055/quizup/170914-201130.757
    170914-153118/quizup/170914-201130.361
    170914-153137/quizup/170914-201250.023
    170914-153158/quizup/170914-201306.037
    170914-153221/quizup/170914-201648.453
    170914-153245/quizup/170914-201252.468 170914-153305/quizup/170914-201050.453"""

  exps = """170914-231951/quizup/170915-032025.411
    170914-232159/quizup/170915-032225.825
    170914-232330/quizup/170915-040616.383
    170914-232350/quizup/170915-040809.867
    170914-232414/quizup/170915-040314.460
    170914-232438/quizup/170915-035913.893
    170914-232501/quizup/170915-040730.774
    170914-232523/quizup/170915-040311.639
    170914-232543/quizup/170915-035747.727"""
  exps = """170915-082816/quizup/170915-131440.110
    170915-082837/quizup/170915-130901.347
    170915-082858/quizup/170915-130841.880
    170915-082920/quizup/170915-130954.426
    170915-082943/quizup/170915-131048.454"""

  # RocksDB log was only for like 10 mins. No sla_admin there.
  exps = """170916-075803/quizup/170916-130854.144"""

  exps = """170916-092153/quizup/170916-132205.868
    170916-092325/quizup/170916-132335.799
    170916-092740/quizup/170916-140616.320
    170916-092804/quizup/170916-141328.769
    170916-092825/quizup/170916-140920.145
    170916-092852/quizup/170916-141053.787
    170916-092915/quizup/170916-141348.288
    170916-092938/quizup/170916-140728.381"""
  exps = """170916-092153/quizup/170916-132205.868"""

  exps = """170916-220723/quizup/170917-020739.228
    170916-220748/quizup/170917-020806.055
    170916-220846/quizup/170917-025257.235
    170916-220910/quizup/170917-025604.621
    170916-220934/quizup/170917-025027.329
    170916-220953/quizup/170917-025025.737
    170916-221014/quizup/170917-025820.759
    170916-221037/quizup/170917-024758.760
    170917-084245/quizup/170917-132036.875
    170917-084309/quizup/170917-132822.408"""
  exps = """170916-220723/quizup/170917-020739.228"""

  exps = """170917-130929/quizup/170917-174607.417
    170917-122717/quizup/170917-162741.599
    170917-123033/quizup/170917-163053.328
    170917-130954/quizup/170917-174637.952
    170917-131020/quizup/170917-174725.221
    170917-131041/quizup/170917-174936.296
    170917-131101/quizup/170917-175045.541
    170917-131124/quizup/170917-175419.171
    170917-131148/quizup/170917-175136.884"""

  # slow dev iops-based control. widh P and varying levels of D.
  exps = """170918-002609/quizup/170918-042726.771
    170918-002740/quizup/170918-042801.188
    170918-002849/quizup/170918-050530.376
    170918-002912/quizup/170918-051309.315
    170918-002934/quizup/170918-050504.193
    170918-002956/quizup/170918-050530.365
    170918-003019/quizup/170918-050834.786
    170918-003039/quizup/170918-050825.371
    170918-003101/quizup/170918-050226.142
    170918-003125/quizup/170918-052241.852
    170918-094956/quizup/170918-144341.674
    170918-095022/quizup/170918-144018.607"""

  # Exploring xr_iops to see if we can get different latencies.
  exps = """170918-180857/quizup/170918-225647.066
    170918-180920/quizup/170918-225506.963
    170918-180944/quizup/170918-225646.945
    170918-181005/quizup/170918-224938.751
    170918-181026/quizup/170918-224942.079
    170918-181047/quizup/170918-230536.228
    170918-181111/quizup/170918-225031.376
    170918-181138/quizup/170918-225625.807
    170918-181200/quizup/170918-225711.266"""

  exps = """170918-222135/quizup/170919-025352.507
    170918-222158/quizup/170919-030120.294
    170918-222220/quizup/170919-030207.986
    170918-222242/quizup/170919-030232.318
    170918-222304/quizup/170919-030717.652
    170918-222327/quizup/170919-030707.413"""

  exps = """170919-124331/quizup/170919-170007.870
    170919-131403/quizup/170919-180125.967
    170919-131424/quizup/170919-180158.349
    170919-131442/quizup/170919-180139.970
    170919-131505/quizup/170919-180424.920
    170919-131524/quizup/170919-180125.980
    170919-131545/quizup/170919-175120.370
    170919-131604/quizup/170919-175703.244"""

  exps = """170919-180328/quizup/170919-223524.568
    170919-180355/quizup/170919-224902.038
    170919-180420/quizup/170919-224852.550
    170919-180442/quizup/170919-224011.441
    170919-180506/quizup/170919-225135.053
    170919-180528/quizup/170919-225115.304
    170919-180548/quizup/170919-224900.713
    170919-180610/quizup/170919-224739.183
    170919-180634/quizup/170919-225207.149
    170919-180655/quizup/170919-225134.893
    170919-180714/quizup/170919-230406.016"""

  # 100K, 150K, 200K. Try lower than 100K
  exps = """170927-094416/quizup/170927-134712.284"""

  if False:
    # Parallel processing
    params = []
    for line in re.split(r"\s+", exps):
      t = line.split("/quizup/")
      if len(t) != 2:
        raise RuntimeError("Unexpected")
      job_id = t[0]
      exp_dt = t[1]
      params.append((job_id, exp_dt))
    p = multiprocessing.Pool(8)
    p.map(Plot, params)
  else:
    for line in re.split(r"\s+", exps):
      t = line.split("/quizup/")
      if len(t) != 2:
        raise RuntimeError("Unexpected")
      job_id = t[0]
      exp_dt = t[1]
      Plot((job_id, exp_dt))


def Plot(param):
  job_id = param[0]
  exp_dt = param[1]
  dn_log_job = "%s/work/mutant/log/quizup/sla-admin/%s" % (os.path.expanduser("~"), job_id)

  fn_log_quizup  = "%s/quizup/%s" % (dn_log_job, exp_dt)
  fn_log_rocksdb = "%s/rocksdb/%s" % (dn_log_job, exp_dt)
  fn_log_dstat   = "%s/dstat/%s.csv" % (dn_log_job, exp_dt)

  log_q = QuizupLog(fn_log_quizup)
  SimTime.Init(log_q.SimTime("simulated_time_begin"), log_q.SimTime("simulated_time_end")
      , log_q.SimTime("simulation_time_begin"), log_q.SimTime("simulation_time_end"))

  qz_std_max = _QzSimTimeDur(log_q.quizup_options["simulation_time_dur_in_sec"])
  qz_opt_str = _QuizupOptionsFormattedStr(log_q.quizup_options)
  error_adj_ranges = log_q.quizup_options["error_adj_ranges"].replace(",", " ")

  (fn_rocksdb_sla_admin_log, pid_params, num_sla_adj) = RocksdbLog.ParseLog(fn_log_rocksdb, exp_dt)

  fn_dstat = DstatLog.GenDataFileForGnuplot(fn_log_dstat, exp_dt)

  fn_out = "%s/sla-admin-by-time-%s.pdf" % (Conf.GetDir("output_dir"), exp_dt)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["STD_MAX"] = qz_std_max
    env["ERROR_ADJ_RANGES"] = error_adj_ranges
    env["IN_FN_QZ"] = fn_log_quizup
    env["IN_FN_SLA_ADMIN"] = "" if num_sla_adj == 0 else fn_rocksdb_sla_admin_log
    env["QUIZUP_OPTIONS"] = qz_opt_str
    env["PID_PARAMS"] = "%s %s %s %s" % (pid_params["target_value"], pid_params["p"], pid_params["i"], pid_params["d"])
    env["WORKLOAD_EVENTS"] = " ".join(str(t) for t in log_q.simulation_time_events)
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
