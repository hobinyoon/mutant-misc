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

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

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

LMARGIN = 10
set sample 1000


# DB IOPS
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "DB IOPS"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  #set logscale y

  plot \
  IN_FN_YCSB u 1:2 w lp pt 7 ps 0.08 lc rgb "red" not
}
# DB IOPS breakdown into reads and writes?  We'll see if it's needed. When you specify target IOPS, it's not needed.


# Total number of SSTables
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "# of SSTables" offset 0.5, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00.000":TIME_MAX]

  C_NUM_SSTS = "red"
  LW_NUM_SSTS = 2

  plot \
  IN_FN_ROCKSDB u 1:4:3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  IN_FN_ROCKSDB u 2:4:(0):($5-$4) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

  # vectors: x y xdelta ydelta
}


# Total SSTable size
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "Total SSTable size (GB)" offset 0.5, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid ytics front lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  Y_MAX=16
  set xrange ["00:00:00.000":TIME_MAX]
  set yrange [0:Y_MAX]

  # Colors of fast and slow storage device
  C0 = "red"
  C1 = "blue"
  C00 = "#FFE8E8"
  C10 = "#E8E8FF"
  TP = 0.1

  LW_NUM_SSTS = 2

  set label "SSTables in fast storage" at graph 0.6, 0.2  front #fc rgb C0
  set label "SSTables in slow storage" at graph 0.6, 0.55 front #fc rgb C0

  do for [i=2:words(TARGET_COST_CHANGES_TIME)] {
    x0 = word(TARGET_COST_CHANGES_TIME, i)
    set arrow from x0, 0 to x0, Y_MAX nohead lc rgb "black" front
  }

  plot \
  IN_FN_ROCKSDB u 1:($4+$5) w filledcurves y1=0 fs noborder solid lc rgb C10 not, \
  IN_FN_ROCKSDB u 1:4       w filledcurves y1=0 fs noborder solid lc rgb C00 not, \
  IN_FN_ROCKSDB u 1:($4+$5) w l lc rgb C1 lw LW_NUM_SSTS not, \
  IN_FN_ROCKSDB u 1:4       w l lc rgb C0 lw LW_NUM_SSTS not
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
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

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
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

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
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  plot IN_FN_MEM u 1:2 w p pt 7 ps 0.08 lc rgb "red" not
}


# Read latency
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Read latency (ms)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

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
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Write latency (ms)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  set logscale y

  bi = 11
  plot \
  IN_FN_YCSB u 1:(column(bi+7)/1000.0) w l smooth bezier lw 3 lc rgb "#FF0000" t "99.99th", \
  IN_FN_YCSB u 1:(column(bi+6)/1000.0) w l smooth bezier lw 3 lc rgb "#BF003F" t "99.9th", \
  IN_FN_YCSB u 1:(column(bi+5)/1000.0) w l smooth bezier lw 3 lc rgb "#7F007F" t "99th", \
  IN_FN_YCSB u 1:(column(bi+4)/1000.0) w l smooth bezier lw 3 lc rgb "#3F00BF" t "90th", \
  IN_FN_YCSB u 1:(column(bi+1)/1000.0) w l smooth bezier lw 3 lc rgb "#0000FF" t "avg"
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

  set xrange ["00:00:00":TIME_MAX]

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

  set xrange ["00:00:00":TIME_MAX]

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

# exit
