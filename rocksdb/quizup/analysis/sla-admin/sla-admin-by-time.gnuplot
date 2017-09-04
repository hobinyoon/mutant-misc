# Tested with gnuplot 4.6 patchlevel 6

IN_FN_QZ = system("echo $IN_FN_QZ")
IN_FN_SLA_ADMIN = system("echo $IN_FN_SLA_ADMIN")
TARGET_LATENCY = system("echo $TARGET_LATENCY") + 0.0
IN_FN_DS = system("echo $IN_FN_DS")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

# TODO: legend

# Number of reads and writes
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set ylabel "Reads/0.5 sec" tc rgb "black"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" #autofreq 0, 500
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set logscale y

  plot \
  IN_FN_QZ u 1:29 w p pt 7 ps 0.2 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:8  w p pt 7 ps 0.2 lc rgb "red" t "write"
}

# EBS st1 disk IOs
if (1) {
  reset

  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "EBS Mag IOPS"

  set logscale y

  plot \
  IN_FN_DS u 25:15 w p pt 7 ps 0.2 lc rgb "blue" t "read", \
  IN_FN_DS u 25:16 w p pt 7 ps 0.2 lc rgb "red" t "write"
}

# Read latency
if (1) {
  reset
  set xdata time
  # 00:00:00.491
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "Read latency (ms)" tc rgb "black"

  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  t_l(x) = TARGET_LATENCY
  set yrange[0:TARGET_LATENCY * 2]

  set key left

  plot \
  IN_FN_QZ u 1:($30/1000) w p pt 7 ps 0.2 lc rgb "#FFB0B0" not, \
  t_l(x) w l lt 1 lw 3 lc rgb "blue" t "Target latency", \
  IN_FN_QZ u 1:($30/1000) w l smooth bezier lw 6 lc rgb "red" not
}


# Latency adjustment
if (1) {
  reset
  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "Latency adjustment (ms)"

  set xrange ["00:00:00.000":]
  #set yrange [:50]

  plot \
  IN_FN_SLA_ADMIN u 1:3 w lp pt 7 ps 0.1 lc rgb "red" not
}

# sst_ott
if (1) {
  reset
  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "SST OTT"

  set xrange ["00:00:00.000":]
  #set yrange [:50]

  plot \
  IN_FN_SLA_ADMIN u 1:4 w lp pt 7 ps 0.1 lc rgb "red" not
}

# Number of SSTables what are/should be in the fast/slow devices
if (1) {
  reset
  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" ( \
      "150"  150 \
    , "100"  100 \
    ,  "50"   50 \
    ,  "0"     0 \
    ,  "50"  -50 \
    , "100" -100 \
    , "150" -150 \
  )
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "Number of SSTables\nin fast/slow stg device"

  set key left

  set xrange ["00:00:00.000":]
  set yrange [-150:150]

  plot \
  IN_FN_SLA_ADMIN u 1:5 w filledcurves y1=0 lc rgb "#FFB0B0" t "Current", \
  IN_FN_SLA_ADMIN u 1:($6*(-1)) w filledcurves y1=0 lc rgb "#B0B0FF" not, \
  IN_FN_SLA_ADMIN u 1:7 w l lc rgb "red" t "Should be", \
  IN_FN_SLA_ADMIN u 1:($8*(-1)) w l lc rgb "blue" not
}
