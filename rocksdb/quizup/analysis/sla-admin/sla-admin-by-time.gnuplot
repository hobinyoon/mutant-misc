# Tested with gnuplot 4.6 patchlevel 6

STD_MAX = system("echo $STD_MAX")
IN_FN_QZ = system("echo $IN_FN_QZ")
IN_FN_SLA_ADMIN = system("echo $IN_FN_SLA_ADMIN")
IN_FN_SLA_ADMIN_FORMAT = system("echo $IN_FN_SLA_ADMIN_FORMAT") + 0
TARGET_LATENCY = system("echo $TARGET_LATENCY") + 0.0
QUIZUP_OPTIONS = system("echo $QUIZUP_OPTIONS")
PID_PARAMS = system("echo $PID_PARAMS")
IN_FN_DS = system("echo $IN_FN_DS")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("QUIZUP_OPTIONS=%s", QUIZUP_OPTIONS)

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

LMARGIN = 10

# Quizup options
if (1) {
  reset
  set noxtics
  set noytics
  set noborder
  f(x) = x
  #set label 1 at screen 0.025, screen 0.90 QUIZUP_OPTIONS font "courier,10" left front
  # Looks better. Feels narrower.
  set label 1 at screen 0.025, screen 0.90 QUIZUP_OPTIONS font "DejaVu Sans Mono,10" left front
  plot f(x) lc rgb "#F0F0F0" not
}


# Number of DB reads and writes
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "DB IO/sec" tc rgb "black"
  set xtics nomirror tc rgb "black"

  logscale_y = 0

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

  # Align the stacked plots
  set lmargin LMARGIN

  if (logscale_y == 1) {
    set logscale y
  }

  set xrange ["00:00:00":STD_MAX]
  set yrange [:10000]

  plot \
  IN_FN_QZ u 1:29 w p pt 7 ps 0.05 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:8  w p pt 7 ps 0.05 lc rgb "red" t "write"
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

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  plot \
  IN_FN_DS u 25:15 w p pt 7 ps 0.1 lc rgb "blue" t "read", \
  IN_FN_DS u 25:16 w p pt 7 ps 0.1 lc rgb "red" t "write"
}

# Read latency: Both Quizup and RocksDB SLA Admin logs have read latencies.
# Go with RocksDB SLA Admin log. It has when the latency is counted in our not.
if (1) {
  reset
  set xdata time
  # 00:00:00.491
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Read latency (ms)" tc rgb "black"

  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  t_l(x) = TARGET_LATENCY
  #set yrange[0:TARGET_LATENCY * 2]
  set yrange[0:200]

  set label sprintf("target latency: %.1f\nPID constants: %s", TARGET_LATENCY, PID_PARAMS) at graph 0.03, graph 0.9

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  use_locksdb_sla_admin_log = 1
  if (use_locksdb_sla_admin_log == 1) {
    plot \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? $2 : 1/0) w p pt 7 ps 0.1 lc rgb "#C0C0C0" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? (TARGET_LATENCY < $2  ? $2 : 1/0) : 1/0) w p pt 7 ps 0.1 lc rgb "#FFC0C0" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? ($2 <= TARGET_LATENCY ? $2 : 1/0) : 1/0) w p pt 7 ps 0.1 lc rgb "#C0C0FF" not, \
    t_l(x) w l lt 1 lc rgb "black" not, \
    IN_FN_SLA_ADMIN u 1:($4 == -1 ? 1/0 : (TARGET_LATENCY < $4  ? $4 : 1/0)) w p pt 7 ps 0.03 lc rgb "red" not, \
    IN_FN_SLA_ADMIN u 1:($4 == -1 ? 1/0 : ($4 <= TARGET_LATENCY ? $4 : 1/0)) w p pt 7 ps 0.03 lc rgb "blue" not
  } else {
    plot \
    IN_FN_QZ u 1:($30/1000) w p pt 7 ps 0.2 lc rgb "#FFB0B0" not, \
    IN_FN_QZ u 1:($30/1000) w l smooth bezier lw 6 lc rgb "red" not, \
    t_l(x) w l lt 1 lc rgb "blue" not
  }
}

# Number of SSTables that are/should be in the fast/slow devices
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
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Number of SSTables\nin fast/slow stg device"

  set key left

  set xrange ["00:00:00.000":]
  #set yrange [-150:150]

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  f(x) = 0

  plot \
  IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : $9) w l lc rgb "#FFC0C0" t "Should be", \
  IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : ($10*(-1))) w l lc rgb "#C0C0FF" not, \
  IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : $7) w l lc rgb "red" t "Actual", \
  IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : ($8*(-1))) w l lc rgb "blue" not, \
  f(x) w l lc rgb "black" not
}

# sst_ott adjustment
if (0) {
  if (IN_FN_SLA_ADMIN ne "") {
    reset
    set border front lc rgb "#808080" back
    set xtics nomirror tc rgb "black"
    set ytics nomirror tc rgb "black"
    set grid xtics ytics back lc rgb "#808080"
    set border front lc rgb "#808080" back

    set xdata time
    set timefmt "%H:%M:%S"
    set format x "%H:%M"

    set xlabel "Time (HH:MM)"
    set ylabel "sst\\_ott adjustment"

    set xrange ["00:00:00.000":]
    #set yrange [:50]

    f(x) = 0

    set lmargin LMARGIN

    set xrange ["00:00:00":STD_MAX]

    if (IN_FN_SLA_ADMIN_FORMAT == 1) {
      plot \
      IN_FN_SLA_ADMIN u 1:3 w filledcurves y1=0 lc rgb "#FFA0A0" not, \
      f(x) w l lc rgb "black" not
    } else {
      set yrange [-1.5:1.5]
      adj_str_to_value(x) = (x eq "move_sst_to_slow" ? -1 : \
        (x eq "move_sst_to_fast" ? 1 : 0) )
      plot \
      IN_FN_SLA_ADMIN u 1:(adj_str_to_value(strcol(5))) w p pt 7 ps 0.2 lc rgb "#FFA0A0" not, \
      f(x) w l lc rgb "black" not
    }
  }
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
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "sst\\_ott"

  set xrange ["00:00:00.000":]

  if (logscale_y == 1) {
    set yrange [0.000001:]
    set logscale y
  }

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  plot \
  IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : $6) w p pt 7 ps 0.1 lc rgb "red" not
}
