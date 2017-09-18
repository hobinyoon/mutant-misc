# Tested with gnuplot 4.6 patchlevel 6

STD_MAX = system("echo $STD_MAX")
ERROR_ADJ_RANGES = system("echo $ERROR_ADJ_RANGES")
IN_FN_QZ = system("echo $IN_FN_QZ")
IN_FN_SLA_ADMIN = system("echo $IN_FN_SLA_ADMIN")
QUIZUP_OPTIONS = system("echo $QUIZUP_OPTIONS")
PID_PARAMS = system("echo $PID_PARAMS")
IN_FN_DS = system("echo $IN_FN_DS")
OUT_FN = system("echo $OUT_FN")

TARGET_VALUE=word(PID_PARAMS, 1) + 0.0

set print "-"
print sprintf("IN_FN_SLA_ADMIN=%s", IN_FN_SLA_ADMIN)
#print sprintf("QUIZUP_OPTIONS=%s", QUIZUP_OPTIONS)
#print sprintf("ERROR_ADJ_RANGES=%s", ERROR_ADJ_RANGES)

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
  set label 1 at screen 0.025, screen 0.90 QUIZUP_OPTIONS font "DejaVu Sans Mono,9" left front
  plot f(x) lc rgb "#F0F0F0" not
}

# EBS st1 IOPS
if (1) {
  reset
  set xdata time
  # 00:00:00.491
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "EBS st1 read IOPS" tc rgb "black"

  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"

  # Horizontal lines for target values
  f_t(x, a) = TARGET_VALUE * (1 + a)

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  logscale_y = 1
  if (logscale_y == 1) {
    set logscale y
    set mytics 10
    label0 = sprintf("Target read IOPS: %.1f" \
      . "\nGray: All IOPS" \
      . "\nBlue: IOPS w/o bg SST activity" \
      . "\nIOPS 0 is shown as 0.2 due to the logscale" \
      , TARGET_VALUE)
  } else {
    set ytics nomirror tc rgb "black"
    label0 = sprintf("Target read IOPS: %.1f" \
      . "\nGray: All IOPS" \
      . "\nBlue: IOPS w/o bg SST activity" \
      , TARGET_VALUE)
  }

  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set label label0 at graph 0.03, graph 0.9 font ",9"

  PS = 0.04

  plot \
  IN_FN_SLA_ADMIN u 1:($6 == 0 ? $7 : 1/0) w p pt 7 ps PS lc rgb "#C0C0C0" not, \
  IN_FN_SLA_ADMIN u 1:($6 == 1 ? ($7 == 0 ? 0.2 : $7) : 1/0) w p pt 7 ps PS lc rgb "blue" not, \
  f_t(x, 0)   w l lt 1 lc rgb "#D0D0D0" not
}

# PID controller adjustment
if (1) {
  reset
  set xdata time
  # 00:00:00.491
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "PID adjustment (relative)" tc rgb "black"

  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" format ("%.1f")

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Adjustment bounds
  ab0 = word(ERROR_ADJ_RANGES, 1) + 0.0
  ab1 = word(ERROR_ADJ_RANGES, 2) + 0.0

  PS = 0.05
  PS1 = 0.1

  set label sprintf( \
    "PID params: %s %s %s" \
    . "\nAdjustment bounds: %s" \
    . "\nBlue: Move an SST to slow dev" \
    . "\nRed: Move an SST to fast dev" \
    , word(PID_PARAMS, 2) \
    , word(PID_PARAMS, 3) \
    , word(PID_PARAMS, 4) \
    , ERROR_ADJ_RANGES) \
    at graph 0.03, graph 0.9 font ",9"

  plot \
  IN_FN_SLA_ADMIN u 1:($6 == 0 ? 1/0 : ($16 < ab0               ? $16 : 1/0)) w p pt 7 ps PS1 lc rgb "red"     not, \
  IN_FN_SLA_ADMIN u 1:($6 == 0 ? 1/0 : (ab0 <= $16 && $16 < ab1 ? $16 : 1/0)) w p pt 7 ps PS  lc rgb "#C0C0C0" not, \
  IN_FN_SLA_ADMIN u 1:($6 == 0 ? 1/0 : (ab1 <= $16              ? $16 : 1/0)) w p pt 7 ps PS1 lc rgb "blue"    not
}

# Number of SSTables that are/should be in the fast/slow devices
if (1) {
  if (IN_FN_SLA_ADMIN ne "") {
    reset
    set xtics nomirror tc rgb "black"
    set ytics nomirror tc rgb "black"
    #set ytics nomirror tc rgb "black" ( \
    #    "200"  200 \
    #  , "150"  150 \
    #  , "100"  100 \
    #  ,  "50"   50 \
    #  ,  "0"     0 \
    #  ,  "50"  -50 \
    #  , "100" -100 \
    #  , "150" -150 \
    #)
    set grid xtics ytics back lc rgb "#808080"
    set border back lc rgb "#808080" back

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

    PS=0.1

    plot \
    f(x) w l lc rgb "black" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : $12) w p pt 7 ps PS lc rgb "#FFC0C0" t "Should be", \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : ($13*(-1))) w p pt 7 ps PS lc rgb "#C0C0FF" not, \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : $10) w p pt 7 ps PS lc rgb "red" t "Actual", \
    IN_FN_SLA_ADMIN u 1:($3 == 0 ? 1/0 : ($11*(-1))) w p pt 7 ps PS lc rgb "blue" not
  }
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
  set border back lc rgb "#808080" back

  f_t(x, a) = TARGET_VALUE * (1 + a)

  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  logscale_y = 1
  if (logscale_y == 1) {
    set logscale y
  } else {
    set yrange[:100]
  }

  set key left

  # TODO: these can go
  # error adj ranges
  ar0 = word(ERROR_ADJ_RANGES, 1) + 0.0
  ar1 = word(ERROR_ADJ_RANGES, 2) + 0.0
  # target values
  tv0 = TARGET_VALUE * (1 + ar0)
  tv1 = TARGET_VALUE * (1 + ar1)

  set label sprintf("Gray: all latencies" \
    . "\nGreen: 10-sec running average of all latencies" \
    . "\nBlue: 400-sec running average of all latencies" \
    . "\nRed: 10-value running avg of latencies w/o bg SST activities" \
    ) at graph 0.03, graph 0.9 font ",9"

  # Point size for latency and runnig average latency
  PS_LAT = 0.04
  PS_LAT_RA = 0.04

  plot \
  IN_FN_SLA_ADMIN u 1:2 w p pt 7 ps PS_LAT lc rgb "#C0C0C0" not, \
  IN_FN_SLA_ADMIN u 1:3 w l lc rgb "green" not, \
  IN_FN_SLA_ADMIN u 1:4 w l lc rgb "blue" not, \
  IN_FN_SLA_ADMIN u 1:($6 == 0 ? 1/0 : $5) w p pt 7 ps PS_LAT lc rgb "red" not

  #IN_FN_SLA_ADMIN u 1:3 w lp pt 7 ps PS_LAT lc rgb "blue" not, \

  #IN_FN_SLA_ADMIN u 1:3 w p pt 7 ps PS_LAT lc rgb "blue" t "10-sec running avg of all latencies", \

  #plot \
  #IN_FN_SLA_ADMIN u 1:($3 == 0 ? $2 : 1/0) w p pt 7 ps PS_LAT lc rgb "#B0B0B0" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? ($2 < tv0 ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#D0D0FF" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? (((tv0 <= $2) && ($2 < tv1)) ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#D0FFD0" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? (tv1 <= $2 ? $2 : 1/0) : 1/0) w p pt 7 ps PS_LAT lc rgb "#FFD0D0" not, \
  #f_t(x, 0)   w l lt 1 lc rgb "#B0B0B0" not, \
  #f_t(x, ar1) w l lt 1 lc rgb "#D0D0D0" not, \
  #f_t(x, ar0) w l lt 1 lc rgb "#D0D0D0" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? ($4 < tv0 ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#0000FF" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? (((tv0 <= $4) && ($4 < tv1)) ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#00FF00" not, \
  #IN_FN_SLA_ADMIN u 1:($3 == 1 ? (tv1 <= $4 ? $4 : 1/0) : 1/0) w p pt 7 ps PS_LAT_RA lc rgb "#FF0000" not
}

# sst_ott
if (1) {
  if (IN_FN_SLA_ADMIN ne "") {
    reset

    logscale_y = 0

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
    set border back lc rgb "#808080" back

    set xdata time
    set timefmt "%H:%M:%S"
    set format x "%H:%M"

    set xlabel "Time (HH:MM)"
    set ylabel "sst\\_ott"

    set xrange ["00:00:00.000":]

    if (logscale_y == 1) {
      set yrange [0.000001:]
      set logscale y
    } else {
      set yrange [0:]
    }

    set lmargin LMARGIN

    set xrange ["00:00:00":STD_MAX]

    # line plot doesn't work since there are holes
    plot \
    IN_FN_SLA_ADMIN u 1:($6 == 0 ? 1/0 : $9) w p pt 7 ps 0.1 lc rgb "red" not
  }
}

# Disk IOPS both Local SSD and EBS st1
if (1) {
  reset

  set xtics nomirror tc rgb "black"

  logscale_y = 1
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
    set yrange [:250]
  }

  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "EBS Mag IOPS\nfrom dstat"

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

  set ylabel "Local SSD IOPS\nfrom dstat"
  plot \
  IN_FN_DS u 25:($14 == 0 ? 1/0 : $14) w p pt 7 ps PS lc rgb "red" t "write (red)", \
  IN_FN_DS u 25:($13 == 0 ? 1/0 : $13) w p pt 7 ps PS lc rgb "blue" t "read (blue)"
}

# Number of DB reads and writes
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "DB IO/sec" tc rgb "black"
  set xtics nomirror tc rgb "black"

  logscale_y = 1

  if (logscale_y == 1) {
    set ytics nomirror tc rgb "black" ( \
        "10^{6}" 1000000 \
      , "10^{5}"  100000 \
      , "10^{4}"   10000 \
      , "10^{3}"    1000 \
      , "10^{2}"     100 \
      , "10^{1}"      10 \
      , "10^{0}"       1 \
    )
    set yrange [:1000000]
  } else {
    set ytics nomirror tc rgb "black"
    set yrange [0:4000]
  }
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  if (logscale_y == 1) {
    set logscale y
  }

  set xrange ["00:00:00":STD_MAX]

  set key left

  plot \
  IN_FN_QZ u 1:($29 == 0 ? 1/0 : $29) w p pt 7 ps 0.05 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:($8  == 0 ? 1/0 : $8 ) w p pt 7 ps 0.05 lc rgb "red" t "write"
}

# sst_ott adjustment
if (0) {
  if (IN_FN_SLA_ADMIN ne "") {
    reset
    set xtics nomirror tc rgb "black"
    set ytics nomirror tc rgb "black"
    set grid xtics ytics back lc rgb "#808080"
    set border back lc rgb "#808080" back

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

    set yrange [-1.5:1.5]
    adj_str_to_value(x) = (x eq "move_sst_to_slow" ? -1 : \
      (x eq "move_sst_to_fast" ? 1 : 0) )
    plot \
    IN_FN_SLA_ADMIN u 1:(adj_str_to_value(strcol(5))) w p pt 7 ps 0.2 lc rgb "#FFA0A0" not, \
    f(x) w l lc rgb "black" not
  }
}

# Memory:cache usage
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Mem:cache (GB)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":STD_MAX]

  plot \
  IN_FN_DS u 25:($18/1048576) w lp pt 7 ps 0.05 lc rgb "red" not
}
