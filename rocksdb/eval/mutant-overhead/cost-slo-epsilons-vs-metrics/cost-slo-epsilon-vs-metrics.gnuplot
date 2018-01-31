# Tested with gnuplot 4.6 patchlevel 6

FN_CSE_VS_ALL = system("echo $FN_CSE_VS_ALL")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("NUM_STGDEVS=%d", NUM_STGDEVS)

set terminal pdfcairo enhanced size 2.8in, (2.3*0.85)in
set output FN_OUT

LMARGIN=0.25
RMARGIN=0.86
#X_MIN = 0.01 / 1.5
X_MIN = -0.01
X_MAX = 0.21

# Storage unit cost
if (1) {
  reset
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "Storage unit cost\n($/GB/month)" offset 0.4,0
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" format "%0.2f" autofreq 0,0.02
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # TODO: set manual mxtics
  if (1) {
  }

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0.28:0.36]

  # Align the stacked plots
  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  set arrow from X_MIN, 0.3 to X_MAX, 0.3 nohead lc rgb "blue" lw 5 lt 0 front
  set label "Cost\nSLO" at X_MAX, 0.3 offset 1,0.5 tc rgb "blue" front

  plot \
  FN_CSE_VS_ALL u 1:2 w p pt 7 ps 0.3 lc rgb "red" not
}

# Total SSTable size migrated
if (1) {
  reset
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "SSTables migrated (GB)"
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" #format "%0.2f" autofreq 0,0.02
  set mytics 2
  set grid xtics ytics front lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0:]

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  plot \
  FN_CSE_VS_ALL u 1:(0   + 2):(0):($16-2) w vectors nohead lc rgb "#8080FF" lw 10 not, \
  FN_CSE_VS_ALL u 1:($16 + 2):(0):($17-2) w vectors nohead lc rgb "#FF8080" lw 10 not
}

# Total SSTable size compacted
if (1) {
  reset
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "SSTables compacted (GB)"
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" autofreq 0,50
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0:]

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  # TODO: Breakdown of blue and red

  plot \
  FN_CSE_VS_ALL u 1:(0   + 2):(0):($12-2) w vectors nohead lc rgb "#8080FF" lw 10 not, \
  FN_CSE_VS_ALL u 1:($12 + 2):(0):($13-2) w vectors nohead lc rgb "#FF8080" lw 10 not, \
  FN_CSE_VS_ALL u 1:($12 + $13 + 2):(0):($10 - $11 -2) w vectors nohead lc rgb "#808080" lw 10 not
}

exit

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
  set grid xtics ytics back lc rgb "#808080"
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
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "# of SSTables" offset 0.5, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
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
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "Total SSTable size (GB)" offset 0.5, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00.000":TIME_MAX]

  C_NUM_SSTS = "red"
  LW_NUM_SSTS = 2

  plot \
  IN_FN_ROCKSDB u 1:6:3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  IN_FN_ROCKSDB u 2:6:(0):($7-$6) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

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
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  if (NUM_STGDEVS == 2) {
    i_x=17
    i_y=10
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
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  if (NUM_STGDEVS == 2) {
    i_x=17
    i_y=19
  } else {
    print sprintf("Unexpected NUM_STGDEVS=%d", NUM_STGDEVS)
    exit
  }

  plot IN_FN_DSTAT u (column(i_x)):(100 - column(i_y)) w p pt 7 ps 0.08 lc rgb "red" not
}


# CPU usage. 1-min average
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "CPU usage (%)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00":TIME_MAX[1:5]]

  plot IN_FN_CPU_AVG u 1:2 w p pt 7 ps 0.08 lc rgb "red" not
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
  set grid xtics ytics back lc rgb "#808080"
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
  set grid xtics ytics back lc rgb "#808080"
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
  set grid xtics ytics back lc rgb "#808080"
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
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  i_x=17
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
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  i_x=17
  i_y=7

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
