# Tested with gnuplot 4.6 patchlevel 6

PARAMS = system("echo $PARAMS")
NUM_STGDEVS = system("echo $NUM_STGDEVS") + 0
TIME_MAX = system("echo $TIME_MAX")
IN_FN_DSTAT = system("echo $IN_FN_DSTAT")
IN_FN_YCSB = system("echo $IN_FN_YCSB")
IN_FN_ROCKSDB = system("echo $IN_FN_ROCKSDB")
IN_FN_CPU_AVG = system("echo $IN_FN_CPU_AVG")
IN_FN_MEM = system("echo $IN_FN_MEM")
TARGET_COST_CHANGES_TIME = system("echo $TARGET_COST_CHANGES_TIME")
TARGET_COST_CHANGES_COST = system("echo $TARGET_COST_CHANGES_COST")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("NUM_STGDEVS=%d", NUM_STGDEVS)
print sprintf("IN_FN_ROCKSDB=%s", IN_FN_ROCKSDB)

# Get ranges
if (1) {
  set terminal unknown
  set xdata time
  set timefmt "%H:%M:%S"

  plot IN_FN_YCSB u 1:2 w l
  #Y_MAX_DB_IOPS=GPVAL_DATA_Y_MAX
  Y_MIN_DB_IOPS=GPVAL_Y_MIN
  Y_MAX_DB_IOPS=GPVAL_Y_MAX

  #show variables all
}


set terminal pdfcairo enhanced size 3.8in, (3.8*0.30)in
set output OUT_FN

LMARGIN = 0.17
set sample 1000

# Hide the SSTable loading phase. Not to distract the reviewers
#TIME_MIN = "00:00:00"
TIME_MIN = "00:00:12"

# autofreq interval
AFI = 15 * 60

# Cost change labels
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"

  set notics
  set noborder

  # Align the stacked plots
  set lmargin screen LMARGIN
  set bmargin screen 0.05

  Y_MAX=1
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [0:Y_MAX]

  LW = 4

  y_t = 0.09
  y_b = 0.0
  y_m = (y_b + y_t) / 2.0

  y_t1 = y_t + 0.10
  y_t2 = y_t1 + 0.15
  y_t3 = y_t2 + 0.15

  set label "Target cost ($/GB/month)" at TIME_MIN, y_t3 offset -1.5, 0 tc rgb "black"
  set label "Initial value" at TIME_MIN, y_t2 offset -1.5, 0 tc rgb "black"
  set label "Changes" at TIME_MIN, y_t2 offset  8.9, 0 tc rgb "black"

  #set arrow from TIME_MIN, y_m to TIME_MAX, y_m nohead lc rgb "black" lw LW front
  do for [i=1:words(TARGET_COST_CHANGES_TIME)] {
    if (i == 1) {
      x0 = TIME_MIN
    } else {
      x0 = word(TARGET_COST_CHANGES_TIME, i)
    }
    set arrow from x0, y_t to x0, y_b head lc rgb "black" lw LW front
    set label word(TARGET_COST_CHANGES_COST, i) at x0, y_t1 center tc rgb "black"
  }

  plot x w l lc rgb "white" not
}


# Line type and width of the vertical cost change lines
LT_CC = 0
LW_CC = 4


# Storage cost
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)" offset 0,0.2
  set ylabel "Storage cost\n($/GB/month)" offset 1, 0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid ytics front lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN
  set tmargin screen 0.96
  set bmargin screen 0.05

  Y_MAX=0.59
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [0:Y_MAX]

  LW = 2

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, 0 to x0, Y_MAX nohead lc rgb "black" lw LW_CC lt LT_CC front
  }

  plot \
  IN_FN_ROCKSDB u 1:6 w l lw LW not
}


# SSTables in fast and slow storage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)" offset 0,0.2
  set ylabel "Total SSTable size\n(GB)" offset 0, 0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black" autofreq 0,5
  set mytics 5
  set grid ytics front lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN
  set tmargin screen 0.98
  set bmargin screen 0.05

  Y_MAX=14.5
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [0:Y_MAX]

  # Colors of fast and slow storage device
  C0 = "red"
  C1 = "blue"
  C00 = "#FFE8E8"
  C10 = "#E8E8FF"

  LW_NUM_SSTS = 2

  x0 = 0.62
  set label "In fast storage" at graph x0, 0.2 front #fc rgb C0
  set label "In slow storage" at graph x0, 0.6 front #fc rgb C0
  #set label "SSTables in slow storage" at graph 0.6, 0.55 front #fc rgb C0

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, 0 to x0, Y_MAX nohead lc rgb "black" lw LW_CC lt LT_CC front
  }

  plot \
  IN_FN_ROCKSDB u 1:($4+$5) w filledcurves y1=0 fs noborder solid lc rgb C10 not, \
  IN_FN_ROCKSDB u 1:4       w filledcurves y1=0 fs noborder solid lc rgb C00 not, \
  IN_FN_ROCKSDB u 1:($4+$5) w l lc rgb C1 lw LW_NUM_SSTS not, \
  IN_FN_ROCKSDB u 1:4       w l lc rgb C0 lw LW_NUM_SSTS not
}


# DB read and write latency
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "DB latency\n(ms)" offset 2,0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN
  set tmargin screen 0.96
  set bmargin screen 0.05

  Y_MIN=0.01
  Y_MAX=90
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [Y_MIN:Y_MAX]

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, Y_MIN to x0, Y_MAX nohead lc rgb "black" lw LW_CC lt LT_CC front
  }

  if (1) {
    x0 = 0.83
    y0 = 0.50
    y_h = 0.10

    x00 = x0 - 0.01
    x1 = x0 + 0.19
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "Read avg" at screen x0,y0 front

    y0 = 0.79
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "Read 99th" at screen x0,y0 front

    y0 = 0.25
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "Write 99th" at screen x0,y0 front

    y0 = 0.15
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "Write avg" at screen x0,y0 front
  }

  set logscale y

  bi_r = 3
  bi_w = 11
  plot \
  IN_FN_YCSB u 1:(column(bi_r+5)/1000.0) w l smooth bezier lw 3 lc rgb "#8080FF" not, \
  IN_FN_YCSB u 1:(column(bi_r+1)/1000.0) w l smooth bezier lw 3 lc rgb "#0000FF" not, \
  IN_FN_YCSB u 1:(column(bi_w+5)/1000.0) w l smooth bezier lw 3 lc rgb "#FF8080" not, \
  IN_FN_YCSB u 1:(column(bi_w+1)/1000.0) w l smooth bezier lw 3 lc rgb "#FF0000" not
}


# Storage cost: Mutant vs. others
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)" offset 0,0.2
  set ylabel "Storage cost\n($/GB/month)" offset 1, 0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid ytics front lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN
  set tmargin screen 0.96
  set bmargin screen 0.05

  Y_MAX=0.59
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [0:Y_MAX]

  LW = 2

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, 0 to x0, Y_MAX nohead lc rgb "black" lw LW_CC lt LT_CC front
  }

  # Color for other organization strategies
  C_l = "blue"
  C_rr = "red"

  y0 = 0.045
  set arrow from TIME_MIN, y0 to TIME_MAX, y0 nohead lc rgb C_l lw LW
  y0 = 0.528
  set arrow from TIME_MIN, y0 to TIME_MAX, y0 nohead lc rgb C_l lw LW

  if (1) {
    # Color for leveled-organization label
    C_lt = "blue"

    x0 = 0.81
    y0 = 0.85
    y_h = 0.12
    x00 = x0 - 0.011
    x1 = x0 + 0.18

    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "L: 0 1 2 3 |" at screen x0,y0 tc rgb C_lt front

    y0 = 0.525
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "L: 0 1 2 | 3" at screen x0,y0 tc rgb C_lt front

    y0 = 0.27
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "L: 0 1 | 2 3" at screen x0,y0 tc rgb C_lt front

    y0 = 0.15
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "L: 0 | 1 2 3" at screen x0,y0 tc rgb C_lt front

    y0 = 0.04
    y00 = y0-(y_h/2)
    y01 = y0+(y_h/2)
    set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "L: | 0 1 2 3" at screen x0,y0 tc rgb C_lt front

    y0 = 0.435
    #y00 = y0-(y_h/2)
    #y01 = y0+(y_h/2)
    #set obj rect from screen x00,y00 to screen x1,y01 fs noborder fc rgb "white" front
    set label "RR" at screen x0,y0 tc rgb C_rr front
  }

  plot \
  IN_FN_ROCKSDB u 1:6  w l lw LW lc rgb "black" not, \
  IN_FN_ROCKSDB u 1:17 w l lw LW lc rgb C_rr not, \
  IN_FN_ROCKSDB u 1:14 w l lw LW lc rgb C_l not, \
  IN_FN_ROCKSDB u 1:15 w l lw LW lc rgb C_l not, \
  IN_FN_ROCKSDB u 1:16 w l lw LW lc rgb C_l not
}


# DB IOPS
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "DB IOPS"
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN

  Y_MIN=Y_MIN_DB_IOPS
  Y_MAX=Y_MAX_DB_IOPS
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [Y_MIN:Y_MAX]

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, Y_MIN to x0, Y_MAX nohead lc rgb "black" lw LW_CC lt LT_CC front
  }

  plot \
  IN_FN_YCSB u 1:2 w lp pt 7 ps 0.08 lc rgb "red" not
}
# DB IOPS breakdown into reads and writes?  We'll see if it's needed. When you specify target IOPS, it's not needed.


# So I can look the top of the screen. My neck hurts.
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Dummy" offset 1,0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  set xrange [TIME_MIN:TIME_MAX]

  set lmargin screen LMARGIN
  do for [i=1:5] {
    plot IN_FN_YCSB u 1:0 w l lc rgb "white" not
  }
}
exit


# Read latency
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Read latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  Y_MIN=0.1
  Y_MAX=200
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [Y_MIN:Y_MAX]

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, Y_MIN to x0, Y_MAX nohead lc rgb "black" front
  }

  set logscale y

  bi=3
  plot \
  IN_FN_YCSB u 1:(column(bi+7)/1000.0) w l smooth bezier lw 3 lc rgb "#FF0000" t "99.99th", \
  IN_FN_YCSB u 1:(column(bi+6)/1000.0) w l smooth bezier lw 3 lc rgb "#BF003F" t "99.9th", \
  IN_FN_YCSB u 1:(column(bi+5)/1000.0) w l smooth bezier lw 3 lc rgb "#7F007F" t "99th", \
  IN_FN_YCSB u 1:(column(bi+4)/1000.0) w l smooth bezier lw 3 lc rgb "#3F00BF" t "90th", \
  IN_FN_YCSB u 1:(column(bi+1)/1000.0) w l smooth bezier lw 3 lc rgb "#0000FF" t "avg"

  # This doesn't help
  #print sprintf("GPVAL_DATA_Y_MAX=%f", GPVAL_DATA_Y_MAX)
}


# Write latency
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Write latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black" autofreq 0, AFI
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  Y_MIN=0.01
  Y_MAX=10
  set xrange [TIME_MIN:TIME_MAX]
  set yrange [Y_MIN:Y_MAX]

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, Y_MIN to x0, Y_MAX nohead lc rgb "black" front
  }

  set logscale y

  bi = 11
  plot \
  IN_FN_YCSB u 1:(column(bi+7)/1000.0) w l smooth bezier lw 3 lc rgb "#FF0000" t "99.99th", \
  IN_FN_YCSB u 1:(column(bi+6)/1000.0) w l smooth bezier lw 3 lc rgb "#BF003F" t "99.9th", \
  IN_FN_YCSB u 1:(column(bi+5)/1000.0) w l smooth bezier lw 3 lc rgb "#7F007F" t "99th", \
  IN_FN_YCSB u 1:(column(bi+4)/1000.0) w l smooth bezier lw 3 lc rgb "#3F00BF" t "90th", \
  IN_FN_YCSB u 1:(column(bi+1)/1000.0) w l smooth bezier lw 3 lc rgb "#0000FF" t "avg"
}


# Total number of SSTables
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "# of SSTables" offset 0.5, 0
  set xtics nomirror tc rgb "black"
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  C_NUM_SSTS = "red"
  LW_NUM_SSTS = 2

  plot \
  IN_FN_ROCKSDB u 1:4:3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  IN_FN_ROCKSDB u 2:4:(0):($5-$4) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

  # vectors: x y xdelta ydelta
}




# Memory:cache usage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "File system cache size (GB)"
  set xtics nomirror tc rgb "black"
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  if (NUM_STGDEVS == 3) {
    i_x=21
    i_y=14
  } else {
    print sprintf("Unexpected NUM_STGDEVS=%d", NUM_STGDEVS)
    exit
  }

  plot IN_FN_DSTAT u (column(i_x)):(column(i_y)/1048576) w lp pt 7 ps 0.08 lc rgb "red" not
}


# CPU usage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "CPU usage (%)"
  set xtics nomirror tc rgb "black"
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  if (NUM_STGDEVS == 3) {
    i_x=21
    i_y=23
  } else {
    print sprintf("Unexpected NUM_STGDEVS=%d", NUM_STGDEVS)
    exit
  }

  plot IN_FN_DSTAT u (column(i_x)):(100 - column(i_y)) w p pt 7 ps 0.08 lc rgb "red" not
}


# CPU usage. 1-min average
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "CPU usage (%)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00":TIME_MAX[1:5]]

  plot IN_FN_CPU_AVG u 1:2 w lp pt 7 ps 0.08 lc rgb "red" not
}


# Memory (RSS) used by the YCSB Java process
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Memory usage (GB)"
  set xtics nomirror tc rgb "black"
  set xtics add ("00:00" TIME_MIN)
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  plot IN_FN_MEM u 1:2 w p pt 7 ps 0.08 lc rgb "red" not
}


# Local SSD IOs in MiB
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "LS Read, Write (MiB/sec)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  i_x=21
  i_y=3

  logscale_y = 1

  PS = 0.07

  if (logscale_y == 1) {
    set logscale y
    plot \
    IN_FN_DSTAT u i_x:(column(i_y)   == 0 ? 1/0 : column(i_y)  /1048576) w p pt 7 ps PS lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:(column(i_y+1) == 0 ? 1/0 : column(i_y+1)/1048576) w p pt 7 ps PS lc rgb "red"  not
  } else {
    plot \
    IN_FN_DSTAT u i_x:(column(i_y)  /1048576) w p pt 7 ps PS lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:(column(i_y+1)/1048576) w p pt 7 ps PS lc rgb "red"  not, \
    IN_FN_DSTAT u i_x:(column(i_y)  /1048576) w l smooth bezier lw 3 lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:(column(i_y+1)/1048576) w l smooth bezier lw 3 lc rgb "red"  not
  }
}


# Local SSD IOs in IOPS
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "LS Read, Write (IOPS)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange [TIME_MIN:TIME_MAX]

  i_x=21
  i_y=9

  logscale_y = 1

  if (logscale_y == 1) {
    set logscale y
    plot \
    IN_FN_DSTAT u i_x:(column(i_y)   == 0 ? 1/0 : column(i_y)  ) w p pt 7 ps 0.05 lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:(column(i_y+1) == 0 ? 1/0 : column(i_y+1)) w p pt 7 ps 0.05 lc rgb "red"  not
  } else {
    plot \
    IN_FN_DSTAT u i_x:column(i_y)   w p pt 7 ps 0.05 lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:column(i_y+1) w p pt 7 ps 0.05 lc rgb "red"  not, \
    IN_FN_DSTAT u i_x:column(i_y)   w l smooth bezier lw 3 lc rgb "blue" not, \
    IN_FN_DSTAT u i_x:column(i_y+1) w l smooth bezier lw 3 lc rgb "red"  not
  }
}


# Experiment parameters
if (1) {
  reset
  set noxtics
  set noytics
  set noborder
  f(x) = x
  #set label 1 at screen 0.025, screen 0.90 PARAMS font "courier,10" left front
  # Looks better. Feels narrower.
  set label 1 at screen 0.025, screen 0.90 PARAMS font "DejaVu Sans Mono,7" left front
  plot f(x) lc rgb "white" not
}

# exit
