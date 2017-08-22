#!/usr/bin/env python

import ast
import os
import pprint
import re
import sys
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Stat

_dn_output = "%s/.output" % os.path.dirname(__file__)


def main(argv):
  #PlotWorkload("a")
  PlotWorkload("d")


def PlotWorkload(workload_type):
  Util.MkDirs(_dn_output)
  #(fn_plot_data_m_ls_st1, fn_plot_data_ind) = GetPlotDataMutant(workload_type, "ls-st1", "~/work/mutant/log/ycsb/workload-%s/mutant-ls-st1" % workload_type)
  (fn_plot_data_m_ls_st1, fn_plot_data_ind) = GetPlotDataMutant(workload_type, "ls-st1", "~/work/mutant/log/ycsb/workload-%s/170822-022606-d-ls-st1-short-exps" % workload_type)
  sys.exit(1)
  (fn_plot_data_r_st1, fn_plot_data_ind) = GetPlotDataRocksdb(workload_type, "st1", "~/work/mutant/log/ycsb/workload-%s/rocksdb-st1" % workload_type)
  (fn_plot_data_r_ls, fn_plot_data_ind)  = GetPlotDataRocksdb(workload_type, "ls", "~/work/mutant/log/ycsb/workload-%s/rocksdb-ls" % workload_type)

  fn_out = "%s/ycsb-%s-thp-vs-latency.pdf" % (_dn_output, workload_type)

  with Cons.MT("Plotting ..."):
    env = os.environ.copy()
    env["FN_ROCKSDB_ST1"] = fn_plot_data_r_st1
    env["FN_ROCKSDB_LS"] = fn_plot_data_r_ls
    env["FN_MUTANT_LS_ST1"] = fn_plot_data_m_ls_st1
    env["FN_OUT"] = fn_out
    Util.RunSubp("gnuplot %s/thrp-vs-lat.gnuplot" % os.path.dirname(__file__), env=env)
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


def GetPlotDataMutant(workload_type, dev_type, dn):
  fn_out = "%s/ycsb-%s-%s" % (_dn_output, workload_type, dev_type)
  fn_out_ind = "%s/ycsb-%s-%s-individual" % (_dn_output, workload_type, dev_type)
  if os.path.isfile(fn_out) and os.path.isfile(fn_out_ind):
    return (fn_out, fn_out_ind)

  with Cons.MT("Generating plot data for %s ..." % dev_type):
    dn = dn.replace("~", os.path.expanduser("~"))
    fn_manifest = "%s/manifest.yaml" % dn
    sstott_targetiops_exps = None
    with open(fn_manifest) as fo:
      sstott_targetiops_exps = yaml.load(fo)
    #Cons.P(pprint.pformat(sstott_targetiops_exps, width=230))

    exp_ycsblog = {}
    with Cons.MT("Parsing YCSB log files ..."):
      for sst_ott, v in sstott_targetiops_exps.iteritems():
        for ti, exps in v.iteritems():
          for e in exps:
            fn = "%s/%s" % (dn, e)
            #Cons.P(fn)
            if not os.path.exists(fn):
              Util.RunSubp("pbzip2 -k -d %s.bz2" % fn)
            ycsb_log = YcsbLog(fn)
            exp_ycsblog[e] = ycsb_log
            #Cons.P(ycsb_log)

    with Cons.MT("Gen individual/avg stat by target IOPSes ..."):
      # Gen individual stat
      fmt = "%9.4f %6d %17s %5.0f" \
          " %5.0f %2.0f %8.0f %2.0f %2.0f %2.0f %4.0f %6.0f %6.0f %7.0f %8.0f" \
          " %5.0f %3.0f %8.0f %2.0f %2.0f %3.0f %5.0f %6.0f %6.0f %7.0f %7.0f"
      header = Util.BuildHeader(fmt, "sst_ott target_iops exp_dt iops" \
          " r_avg r_min r_max r_1 r_5 r_50 r_90 r_95 r_99 r_99.9 r_99.99" \
          " w_avg w_min w_max w_1 w_5 w_50 w_90 w_95 w_99 w_99.9 w_99.99")
      with open(fn_out_ind, "w") as fo:
        fo.write("# Latency in us\n")
        i = 0
        for sst_ott, v in sorted(sstott_targetiops_exps.iteritems()):
          for ti, exps in sorted(v.iteritems()):
            for e in exps:
              if i % 40 == 0:
                fo.write(header + "\n")
              y = exp_ycsblog[e]
              #Cons.P(e)
              fo.write((fmt + "\n") % (sst_ott, ti, y.exp_dt, y.op_sec
                 , y.r_avg, y.r_min, y.r_max, y.r_1, y.r_5, y.r_50, y.r_90, y.r_95, y.r_99, y.r_999, y.r_9999
                 , y.w_avg, y.w_min, y.w_max, y.w_1, y.w_5, y.w_50, y.w_90, y.w_95, y.w_99, y.w_999, y.w_9999
                 ))
              i += 1
      Cons.P("Created %s %d" % (fn_out_ind, os.path.getsize(fn_out_ind)))

      # Gen average stat
      with open(fn_out, "w") as fo:
        fmt = "%9.4f %6d %6.0f" \
            " %5.0f %2d %8d %2d %2d %2d %4d %5d %6d %7d %7d" \
            " %4.0f %2d %8d %2d %2d %3d %4d %5d %5d %7d %7d" \
            " %1d"
        header = Util.BuildHeader(fmt, "sst_ott target_iops iops" \
            " r_avg r_min r_max r_1p r_5p r_50p r_90p r_95p r_99p r_99.9p r_99.99p" \
            " w_avg w_min w_max w_1p w_5p w_50p w_90p w_95p w_99p w_99.9p w_99.99p" \
            " num_exps" \
            )
        fo.write("# Latency in us\n")
        fo.write("#\n")

        i = 0
        for sst_ott, v in sorted(sstott_targetiops_exps.iteritems()):
          for ti, exps in sorted(v.iteritems()):
            if i % 40 == 0:
              fo.write(header + "\n")
            yas = YcsbAvgStat()
            for e in exps:
              yas.Add(exp_ycsblog[e])
            yas.Calc()
            #Cons.P(yas)
            fo.write((fmt + "\n") % (sst_ott, ti, yas.op_sec
               , yas.r_avg, yas.r_min, yas.r_max, yas.r_1, yas.r_5, yas.r_50, yas.r_90, yas.r_95, yas.r_99, yas.r_999, yas.r_9999
               , yas.w_avg, yas.w_min, yas.w_max, yas.w_1, yas.w_5, yas.w_50, yas.w_90, yas.w_95, yas.w_99, yas.w_999, yas.w_9999
               , len(yas.logs)
               ))
            i += 1
          fo.write("\n")
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
      return (fn_out, fn_out_ind)


def GetPlotDataRocksdb(workload_type, dev_type, dn):
  fn_out = "%s/ycsb-%s-%s" % (_dn_output, workload_type, dev_type)
  fn_out_ind = "%s/ycsb-%s-%s-individual" % (_dn_output, workload_type, dev_type)
  if os.path.isfile(fn_out) and os.path.isfile(fn_out_ind):
    return (fn_out, fn_out_ind)

  with Cons.MT("Generating plot data for %s ..." % dev_type):
    dn = dn.replace("~", os.path.expanduser("~"))
    fn_manifest = "%s/manifest.yaml" % dn
    Cons.P(fn_manifest)
    targetiops_exps = None
    with open(fn_manifest) as fo:
      targetiops_exps = yaml.load(fo)
    #Cons.P(pprint.pformat(targetiops_exps, width=230))

    exp_ycsblog = {}
    with Cons.MT("Parsing YCSB log files ..."):
      for ti, exps in targetiops_exps.iteritems():
        for e in exps:
          fn = "%s/%s" % (dn, e)
          #Cons.P(fn)
          if not os.path.exists(fn):
            Util.RunSubp("pbzip2 -k -d %s.bz2" % fn)
          ycsb_log = YcsbLog(fn)
          exp_ycsblog[e] = ycsb_log
          #Cons.P(ycsb_log)

    with Cons.MT("Gen individual/avg stat by target IOPSes ..."):
      # Gen individual stat
      with open(fn_out_ind, "w") as fo:
        fmt = "%5d %17s %5.0f" \
            " %5.0f %3.0f %8.0f %2.0f %2.0f %2.0f %4.0f %6.0f %6.0f %7.0f %7.0f" \
            " %5.0f %3.0f %8.0f %2.0f %2.0f %2.0f %5.0f %6.0f %6.0f %7.0f %7.0f"
        fo.write("# Latency in us\n")
        fo.write("%s\n" % Util.BuildHeader(fmt, "target_iops exp_dt iops" \
            " r_avg r_min r_max r_1 r_5 r_50 r_90 r_95 r_99 r_99.9 r_99.99" \
            " w_avg w_min w_max w_1 w_5 w_50 w_90 w_95 w_99 w_99.9 w_99.99"))
        for ti, exps in sorted(targetiops_exps.iteritems()):
          for e in exps:
            y = exp_ycsblog[e]
            #Cons.P(e)
            fo.write((fmt + "\n") % (ti, y.exp_dt, y.op_sec
               , y.r_avg, y.r_min, y.r_max, y.r_1, y.r_5, y.r_50, y.r_90, y.r_95, y.r_99, y.r_999, y.r_9999
               , y.w_avg, y.w_min, y.w_max, y.w_1, y.w_5, y.w_50, y.w_90, y.w_95, y.w_99, y.w_999, y.w_9999
               ))
      Cons.P("Created %s %d" % (fn_out_ind, os.path.getsize(fn_out_ind)))

      # Gen average stat
      with open(fn_out, "w") as fo:
        fmt = "%6d %6.0f" \
            " %5.0f %2d %8d %2d %2d %2d %5d %6d %7d %7d %8d" \
            " %5.0f %2d %8d %2d %2d %2d %5d %6d %7d %7d %7d" \
            " %1d"
        header = Util.BuildHeader(fmt, "target_iops iops" \
            " r_avg r_min r_max r_1p r_5p r_50p r_90p r_95p r_99p r_99.9p r_99.99p" \
            " w_avg w_min w_max w_1p w_5p w_50p w_90p w_95p w_99p w_99.9p w_99.99p" \
            " num_exps" \
            )
        fo.write("# Latency in us\n")
        fo.write("#\n")
        fo.write(header + "\n")

        for ti, exps in sorted(targetiops_exps.iteritems()):
          yas = YcsbAvgStat()
          for e in exps:
            yas.Add(exp_ycsblog[e])
          yas.Calc()
          #Cons.P(yas)
          fo.write((fmt + "\n") % (ti, yas.op_sec
             , yas.r_avg, yas.r_min, yas.r_max, yas.r_1, yas.r_5, yas.r_50, yas.r_90, yas.r_95, yas.r_99, yas.r_999, yas.r_9999
             , yas.w_avg, yas.w_min, yas.w_max, yas.w_1, yas.w_5, yas.w_50, yas.w_90, yas.w_95, yas.w_99, yas.w_999, yas.w_9999
             , len(yas.logs)
             ))
      Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
      return (fn_out, fn_out_ind)


class YcsbLog:
  def __init__(self, fn):
    self.fn = fn
    fn0 = os.path.basename(fn)
    #Cons.P(fn0)

    mo = re.match(r"(?P<v>\d\d\d\d\d\d-\d\d\d\d\d\d\.\d\d\d)-[a-f]", fn0)
    if mo is None:
      raise RuntimeError("Unexpected")
    self.exp_dt = mo.group("v")

    with open(fn) as fo:
      for line in fo:
        #Cons.P(line)
        if line.startswith("Command line: "):
          self._ParseOptions(line)
          continue

        elif line.startswith("params = {"):
          pass

        elif line.startswith("run = {"):
          self.run_options = ast.literal_eval(line[6:])
          self.sst_ott = float(self.run_options["mutant_options"]["sst_ott"])

        elif line.startswith("[READ], "):
          # In us
          # [READ], Average, 9720.066147407726
          # [READ], Min, 2
          # [READ], Max, 12472479
          # [READ], p1, 3
          # [READ], p5, 3
          # [READ], p50, 5
          # [READ], p90, 119
          # [READ], p95, 175
          # [READ], p99, 266929
          # [READ], p99.9, 1263474
          # [READ], p99.99, 2521401
          mo = re.match(r"\[READ\], Average, (?P<v>(\d|\.)+).*", line)
          if mo is not None:
            self.r_avg = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], Min, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_min = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], Max, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_max = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p1, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_1 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p5, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_5 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p50, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_50 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p90, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_90 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p95, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_95 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_99 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99\.9, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_999 = float(mo.group("v"))
            continue
          mo = re.match(r"\[READ\], p99\.99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.r_9999 = float(mo.group("v"))
            continue
        elif line.startswith("[INSERT], "):
          mo = re.match(r"\[INSERT\], Average, (?P<v>(\d|\.)+).*", line)
          if mo is not None:
            self.w_avg = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], Min, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_min = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], Max, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_max = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p1, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_1 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p5, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_5 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p50, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_50 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p90, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_90 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p95, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_95 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_99 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99\.9, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_999 = float(mo.group("v"))
            continue
          mo = re.match(r"\[INSERT\], p99\.99, (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.w_9999 = float(mo.group("v"))
            continue
        elif line.startswith("[OVERALL], "):
          mo = re.match(r"\[OVERALL\], Throughput\(ops\/sec\), (?P<v>(\d|\.)+)", line)
          if mo is not None:
            self.op_sec = float(mo.group("v"))
            continue

  def _ParseOptions(self, line):
    # -db com.yahoo.ycsb.db.RocksDBClient -s -P workloads/workloadd -p rocksdb.dir=/mnt/local-ssd1/rocksdb-data/ycsb -threads 100 -p
    # status.interval=1 -p fieldcount=10 -p fieldlength=100 -p readproportion=0.95 -p insertproportion=0.05 -p recordcount=10000000 -p
    # operationcount=30000000 -p readproportion=0.95 -p insertproportion=0.05 -target 130000 -t
    mo = re.match(r".+ -P workloads/workload(?P<workload_type>[a-f])" \
        ".* -target (?P<target_iops>\d+).*", line)
    # Make sure it's workload d
    self.workload_type = mo.group("workload_type")
    self.target_iops = int(mo.group("target_iops"))

  def __repr__(self):
    return " ".join("%s=%s" % (k, v) for k, v in sorted(vars(self).iteritems()))


class YcsbAvgStat:
  def __init__(self):
    self.logs = []

  def Add(self, ycsb_log):
    self.logs.append(ycsb_log)

  def Calc(self):
    op_sec = []
    r_1 = []
    r_5 = []
    r_50 = []
    r_90 = []
    r_95 = []
    r_99 = []
    r_999 = []
    r_9999 = []
    r_avg = []
    r_max = []
    r_min = []
    w_1 = []
    w_5 = []
    w_50 = []
    w_90 = []
    w_95 = []
    w_99 = []
    w_999 = []
    w_9999 = []
    w_avg = []
    w_max = []
    w_min = []
    for l in self.logs:
      # exp_dt=170805-233212.730 fn=/home/hobin/work/mutant/log/ycsb/d-thrp-vs-lat/rocksdb-st1/good/170805-180749/ycsb/170805-233212.730-d
      # op_sec=9902.92165898 r_1=3.0 r_5=3.0 r_50=7.0 r_90=135.0 r_95=207.0 r_99=257710.0 r_999=1222746.0 r_9999=2552744.0
      # r_avg=9529.4250367 r_max=14803272.0 r_min=2.0 target_iops=10000 w_1=15.0 w_5=17.0 w_50=26.0 w_90=54.0 w_95=80.0 w_99=274649.0
      # w_999=933013.0 w_9999=2261246.0 w_avg=8020.84528045 w_max=4506480.0 w_min=11.0
      op_sec.append(l.op_sec)
      r_1   .append(l.r_1   )
      r_5   .append(l.r_5   )
      r_50  .append(l.r_50  )
      r_90  .append(l.r_90  )
      r_95  .append(l.r_95  )
      r_99  .append(l.r_99  )
      r_999 .append(l.r_999 )
      r_9999.append(l.r_9999)
      r_avg .append(l.r_avg )
      r_max .append(l.r_max )
      r_min .append(l.r_min )
      w_1   .append(l.w_1   )
      w_5   .append(l.w_5   )
      w_50  .append(l.w_50  )
      w_90  .append(l.w_90  )
      w_95  .append(l.w_95  )
      w_99  .append(l.w_99  )
      w_999 .append(l.w_999 )
      w_9999.append(l.w_9999)
      w_avg .append(l.w_avg )
      w_max .append(l.w_max )
      w_min .append(l.w_min )
    self.op_sec = sum(op_sec) / len(op_sec)
    self.r_1    = sum(r_1   ) / len(r_1   )
    self.r_5    = sum(r_5   ) / len(r_5   )
    self.r_50   = sum(r_50  ) / len(r_50  )
    self.r_90   = sum(r_90  ) / len(r_90  )
    self.r_95   = sum(r_95  ) / len(r_95  )
    self.r_99   = sum(r_99  ) / len(r_99  )
    self.r_999  = sum(r_999 ) / len(r_999 )
    self.r_9999 = sum(r_9999) / len(r_9999)
    self.r_avg  = sum(r_avg ) / len(r_avg )
    self.r_max  = sum(r_max ) / len(r_max )
    self.r_min  = sum(r_min ) / len(r_min )
    self.w_1    = sum(w_1   ) / len(w_1   )
    self.w_5    = sum(w_5   ) / len(w_5   )
    self.w_50   = sum(w_50  ) / len(w_50  )
    self.w_90   = sum(w_90  ) / len(w_90  )
    self.w_95   = sum(w_95  ) / len(w_95  )
    self.w_99   = sum(w_99  ) / len(w_99  )
    self.w_999  = sum(w_999 ) / len(w_999 )
    self.w_9999 = sum(w_9999) / len(w_9999)
    self.w_avg  = sum(w_avg ) / len(w_avg )
    self.w_max  = sum(w_max ) / len(w_max )
    self.w_min  = sum(w_min ) / len(w_min )

  def __repr__(self):
    #return " ".join("%s=%s" % (k, v) for k, v in sorted(vars(self).iteritems()))

    kv = {}
    for k, v in sorted(vars(self).iteritems()):
      if k.startswith("r_") or k.startswith("w_"):
        kv[k] = v
    return " ".join("%s=%s" % (k, v) for k, v in sorted(kv.iteritems()))


if __name__ == "__main__":
  sys.exit(main(sys.argv))
