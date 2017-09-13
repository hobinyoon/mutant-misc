# Tested with gnuplot 4.6 patchlevel 6

STD_MAX = system("echo $STD_MAX")
QZ_SST_OTT_ADJ_RANGES = system("echo $QZ_SST_OTT_ADJ_RANGES")
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
#print sprintf("QZ_SST_OTT_ADJ_RANGES=%s", QZ_SST_OTT_ADJ_RANGES)

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

# Memory:cache usage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Mem:cache (GB)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  plot \
  IN_FN_DS u 25:($18/1048576) w lp pt 7 ps 0.05 lc rgb "red" not
}

# EBS st1 disk IOs
if (1) {
  reset

  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"

  logscale_y = 0
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
    set logscale y
  } else {
    set ytics nomirror tc rgb "black"
    set yrange [:100]
  }

  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "EBS Mag IOPS"

  set key left

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  # A gray background box indicating disk reads from DB records reads, not from the SSTable movements.
  if (0) {
    y0 = 25
    y1 = 55
    set object rect from "00:00:00",y0 to STD_MAX,y1 fs solid 0.1 noborder fc rgb "black" behind
    set label "Expected total (fast+slow) disk reads\nIOPS range from DB reads" at "00:02:00",((y0 + y1)/2.0) font ",9"
  }

  PS=0.05

  plot \
  IN_FN_DS u 25:($16 == 0 ? 1/0 : $16) w p pt 7 ps PS lc rgb "red" t "write (red)", \
  IN_FN_DS u 25:($15 == 0 ? 1/0 : $15) w p pt 7 ps PS lc rgb "blue" t "read (blue)"

  set ylabel "Local SSD IOPS"
  plot \
  IN_FN_DS u 25:($14 == 0 ? 1/0 : $14) w p pt 7 ps PS lc rgb "red" t "write (red)", \
  IN_FN_DS u 25:($13 == 0 ? 1/0 : $13) w p pt 7 ps PS lc rgb "blue" t "read (blue)"
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

  f_t(x, a) = TARGET_LATENCY * (1 + a)

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  logscale_y = 0
  if (logscale_y == 1) {
    set logscale y
  } else {
    set yrange[:100]
  }

  use_locksdb_sla_admin_log = 1
  if (use_locksdb_sla_admin_log == 1) {
    # sst_ott adj ranges
    ar0 = word(QZ_SST_OTT_ADJ_RANGES, 1) + 0.0
    ar1 = word(QZ_SST_OTT_ADJ_RANGES, 2) + 0.0
    lat_0 = TARGET_LATENCY * (1 + ar0)
    lat_1 = TARGET_LATENCY * (1 + ar1)

    # Point size for latency and runnig average latency
    PS_LAT = 0.04
    PS_LAT_RA = 0.04

    set label sprintf("target latency: %.1f\nsst\\_ott adj ranges: %.1f %.1f (%s)", \
      TARGET_LATENCY, lat_0, lat_1, QZ_SST_OTT_ADJ_RANGES) at graph 0.03, graph 0.9

    plot \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? $2 : 1/0) w p pt 7 ps PS_LAT lc rgb "#B0B0B0" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? ($2 < lat_0 ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#D0D0FF" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? (((lat_0 <= $2) && ($2 < lat_1)) ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#D0FFD0" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? (lat_1 <= $2 ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#FFD0D0" not, \
    f_t(x, 0)   w l lt 1 lc rgb "#B0B0B0" not, \
    f_t(x, ar1) w l lt 1 lc rgb "#D0D0D0" not, \
    f_t(x, ar0) w l lt 1 lc rgb "#D0D0D0" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? ($4 < lat_0 ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#0000FF" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? (((lat_0 <= $4) && ($4 < lat_1)) ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#00FF00" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 1 ? (lat_1 <= $4 ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#FF0000" not
  } else {
    plot \
    IN_FN_QZ u 1:($30/1000) w p pt 7 ps 0.2 lc rgb "#FFB0B0" not, \
    IN_FN_QZ u 1:($30/1000) w l smooth bezier lw 6 lc rgb "red" not, \
    f_t(x, 0) w l lt 1 lc rgb "blue" not
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
  IN_FN_QZ u 1:($29 == 0 ? 1/0 : $29) w p pt 7 ps 0.05 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:($8  == 0 ? 1/0 : $8 ) w p pt 7 ps 0.05 lc rgb "red" t "write"
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
