
def GetFnCpu():
  fn_out = "%s/cpu-overhead-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  dn_base = Conf.GetDir("dn_base")
  fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
  fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get("computation_overhead"))

  hour_cpustat_0 = _GetCpuStatByHour(fn_ycsb_0)
  hour_cpustat_1 = _GetCpuStatByHour(fn_ycsb_1)
  #Cons.P(hour_cpustat_0)
  #Cons.P(hour_cpustat_1)

  with open(fn_out, "w") as fo:
    fo.write("# u: unmodified\n")
    fo.write("# c: with SSTable access monitoring and SSTable placement computation\n")
    fo.write("#\n")
    fmt = "%2d" \
        " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f" \
        " %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f"
    fo.write(Util.BuildHeader(fmt, "hour" \
        " u_avg u_min u_1 u_25 u_50 u_75 u_99 u_max" \
        " c_avg c_min c_1 c_25 c_50 c_75 c_99 c_max"
        ) + "\n")
    for h, s0 in sorted(hour_cpustat_0.iteritems()):
      s1 = hour_cpustat_1[h]
      fo.write((fmt + "\n") % (h
        , s0.avg, s0.min, s0._1, s0._25, s0._50, s0._75, s0._99, s0.max
        , s1.avg, s1.min, s1._1, s1._25, s1._50, s1._75, s1._99, s1.max
        ))
  Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


def GetFnMem():
  fn_out = "%s/memory-overhead-by-time" % Conf.GetOutDir()
  if os.path.exists(fn_out):
    return fn_out

  with Cons.MT("Generating file for memory overhead plotting ..."):
    dn_base = Conf.GetDir("dn_base")
    fn_ycsb_0 = "%s/%s" % (dn_base, Conf.Get("unmodified_db"))
    fn_ycsb_1 = "%s/%s" % (dn_base, Conf.Get("computation_overhead"))

    hour_memstat_0 = _GetMemStatByHour(fn_ycsb_0)
    hour_memstat_1 = _GetMemStatByHour(fn_ycsb_1)
    #Cons.P(hour_memstat_0)
    #Cons.P(hour_memstat_1)

    with open(fn_out, "w") as fo:
      fo.write("# u: unmodified\n")
      fo.write("# c: with SSTable access monitoring and SSTable placement computation\n")
      fo.write("#\n")
      fmt = "%2d" \
          " %10d %10d %10d %10d %10d %10d %10d %10d" \
          " %10d %10d %10d %10d %10d %10d %10d %10d"
      fo.write(Util.BuildHeader(fmt, "hour" \
          " u_avg u_min u_1 u_25 u_50 u_75 u_99 u_max" \
          " c_avg c_min c_1 c_25 c_50 c_75 c_99 c_max"
          ) + "\n")
      for h, s0 in sorted(hour_memstat_0.iteritems()):
        s1 = hour_memstat_1[h]
        fo.write((fmt + "\n") % (h
          , s0.avg, s0.min, s0._1, s0._25, s0._50, s0._75, s0._99, s0.max
          , s1.avg, s1.min, s1._1, s1._25, s1._50, s1._75, s1._99, s1.max
          ))
    Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
  return fn_out


