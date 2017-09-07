# Tested with gnuplot 4.6 patchlevel 6

IN_FN_QZ = system("echo $IN_FN_QZ")
IN_FN_SLA_ADMIN = system("echo $IN_FN_SLA_ADMIN")
TARGET_LATENCY = system("echo $TARGET_LATENCY") + 0.0
QUIZUP_OPTIONS = system("echo $QUIZUP_OPTIONS")
PID_PARAMS = system("echo $PID_PARAMS")
IN_FN_DS = system("echo $IN_FN_DS")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("QUIZUP_OPTIONS=%s", QUIZUP_OPTIONS)

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

# TODO: legend

# Quizup options
if (1) {
  reset
  set noxtics
  set noytics
  set noborder
  f(x) = x
  set label 1 at screen 0.025, screen 0.90 QUIZUP_OPTIONS font "courier,9" left front
  plot f(x) lc rgb "#F0F0F0" not
}


# Number of reads and writes
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  logscale_y = 0

  set ylabel "Reads/sec" tc rgb "black"
  set xtics nomirror tc rgb "black"

  if (logscale_y == 1) {
    set ytics nomirror tc rgb "black" ( \
        "10^{3}"  1000 \
      , "10^{2}"   100 \
      , "10^{1}"    10 \
      , "10^{0}"     1 \
    )
  } else {
    set ytics nomirror tc rgb "black"
  }
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  if (logscale_y == 1) {
    set logscale y
  }

  plot \
  IN_FN_QZ u 1:29 w p pt 7 ps 0.2 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:8  w p pt 7 ps 0.2 lc rgb "red" t "write"
}

# EBS st1 disk IOs
if (1) {
  reset

  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" ( \
      "10^{3}"  1000 \
    , "10^{2}"   100 \
    , "10^{1}"    10 \
    , "10^{0}"     1 \
    , "10^{-1}"    0.1 \
    , "10^{-2}"    0.01 \
    , "10^{-3}"    0.001 \
    , "10^{-4}"    0.0001 \
    , "10^{-5}"    0.00001 \
    , "10^{-6}"    0.000001 \
  )
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "EBS Mag IOPS"

  set key left

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
  #set yrange[0:TARGET_LATENCY * 2]
  set yrange[0:60]

  set label sprintf("target latency: %.1f\nPID constants: %s", TARGET_LATENCY, PID_PARAMS) at graph 0.03, graph 0.9

  plot \
  IN_FN_QZ u 1:($30/1000) w p pt 7 ps 0.2 lc rgb "#FFB0B0" not, \
  IN_FN_QZ u 1:($30/1000) w l smooth bezier lw 6 lc rgb "red" not, \
  t_l(x) w l lt 1 lc rgb "blue" not
}


# sst_ott adjustment
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
  set ylabel "sst\\_ott adjustment"

  set xrange ["00:00:00.000":]
  #set yrange [:50]

  f(x) = 0

  plot \
  IN_FN_SLA_ADMIN u 1:3 w filledcurves y1=0 lc rgb "#FFA0A0" not, \
  f(x) w l lc rgb "black" not

  #IN_FN_SLA_ADMIN u 1:3 w lp pt 7 ps 0.1 lc rgb "red" not, \

}

# sst_ott
if (1) {
  reset

  logscale_y = 0

  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  if (logscale_y == 1) {
    set ytics nomirror tc rgb "black" ( \
        "10^{3}"  1000 \
      , "10^{2}"   100 \
      , "10^{1}"    10 \
      , "10^{0}"     1 \
      , "10^{-1}"    0.1 \
      , "10^{-2}"    0.01 \
      , "10^{-3}"    0.001 \
      , "10^{-4}"    0.0001 \
      , "10^{-5}"    0.00001 \
      , "10^{-6}"    0.000001 \
    )
  } else {
    set ytics nomirror tc rgb "black"
  }
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "sst\\_ott"

  set xrange ["00:00:00.000":]

  if (logscale_y == 1) {
    set yrange [0.000001:]
    set logscale y
  }

  plot \
  IN_FN_SLA_ADMIN u 1:4 w lp pt 7 ps 0.1 lc rgb "red" not
  #IN_FN_SLA_ADMIN u 1:4 w l smooth bezier lc rgb "red" not
}

# Number of SSTables what are/should be in the fast/slow devices
if (1) {
  reset
  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" ( \
      "200"  200 \
    , "150"  150 \
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
  #set yrange [-150:150]

  plot \
  IN_FN_SLA_ADMIN u 1:5 w filledcurves y1=0 lc rgb "#FFB0B0" t "Current", \
  IN_FN_SLA_ADMIN u 1:($6*(-1)) w filledcurves y1=0 lc rgb "#B0B0FF" not, \
  IN_FN_SLA_ADMIN u 1:7 w l lc rgb "red" t "Should be", \
  IN_FN_SLA_ADMIN u 1:($8*(-1)) w l lc rgb "blue" not
}
