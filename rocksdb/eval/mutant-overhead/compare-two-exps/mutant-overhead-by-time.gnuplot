# Tested with gnuplot 4.6 patchlevel 6

TIME_MAX = system("echo $TIME_MAX")
CPU_STAT = system("echo $CPU_STAT")
FN_CPU_1MIN_AVG = system("echo $FN_CPU_1MIN_AVG")
MEM_STAT = system("echo $MEM_STAT")
ROCKSDB0 = system("echo $ROCKSDB0")
# TODO
ROCKSDB1 = system("echo $ROCKSDB1")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 3.0in, (2.3*0.65)in
set output OUT_FN

LMARGIN = 8.5

# Time vs. total number of SSTables
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
  ROCKSDB0 u 1:4:3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  ROCKSDB0 u 2:4:(0):($5-$4) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

  # vectors: x y xdelta ydelta
}


# Time vs. CPU usage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "CPU usage (%)" offset 0.5,0
  set xtics nomirror tc rgb "black" #autofreq 0,2*3600
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:100]

  PS = 0.1

  # Blue and red
  c0(a) = (a == 0 ? 255 : 255 * 256 * 256)

  plot FN_CPU_1MIN_AVG u 1:2:(c0($3)) w p pt 7 ps PS lc rgb variable not
}


# Time vs. CPU usage. Hourly stat
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "CPU usage (%)" offset 0.5,0
  set xtics nomirror tc rgb "black" #autofreq 0,2*3600
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin LMARGIN

  set xrange ["00:00:00.000":TIME_MAX]
  set yrange [0:100]

  C_U = "blue"
  C_C = "red"

  # CPU usage line width
  C_LW = 2

  # Base indices of columes without and wit CPU
  b0 = 2
  b1 = 10

  # x offset in minutes
  x_offset = 10
  x0(a) = sprintf("%02d:%02d:00", a, 30 - x_offset)
  x1(a) = sprintf("%02d:%02d:00", a, 30 + x_offset)

  set boxwidth 15 * 60
  PS = 0.4

  # Whiskers can represnt either 1st and 99th percentiles or min and max.
  whisker_1_99 = 0

  o0 = 3
  o3 = 5
  if (whisker_1_99) {
    o1 = 2
    o2 = 6
  } else {
    o1 = 1
    o2 = 7
  }

  plot \
  CPU_STAT u (x0($1)):(column(b0+o0)):(column(b0+o1)):(column(b0+o2)):(column(b0+o3)) w candlesticks whiskerbars lc rgb C_U lw C_LW not, \
  CPU_STAT u (x0($1)):(column(b0)) w p pt 7 ps PS lc rgb C_U not, \
  CPU_STAT u (x1($1)):(column(b1+o0)):(column(b0+o1)):(column(b0+o2)):(column(b0+o3)) w candlesticks whiskerbars lc rgb C_C lw C_LW not, \
  CPU_STAT u (x1($1)):(column(b1)) w p pt 7 ps PS lc rgb C_C not

  # candlesticks: x box_min whisker_min whisker_high box_high
}


# Time vs. memory usage
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "Memory usage (GB)" offset -0.5,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" format "%.1f"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin LMARGIN

  set xrange ["00:00:00.000":TIME_MAX]
  #set yrange [0:100]

  C_U = "blue"
  C_C = "red"

  # CPU usage line width
  C_LW = 2

  # Base indices of columes without and wit CPU
  b0 = 2
  b1 = 10

  # x offset in minutes
  x_offset = 10
  x0(a) = sprintf("%02d:%02d:00", a, 30 - x_offset)
  x1(a) = sprintf("%02d:%02d:00", a, 30 + x_offset)

  set boxwidth 15 * 60
  PS = 0.4

  # Whiskers can represnt either 1st and 99th percentiles or min and max.
  whisker_1_99 = 0

  o0 = 3
  o3 = 5
  if (whisker_1_99) {
    o1 = 2
    o2 = 6
  } else {
    o1 = 1
    o2 = 7
  }

  plot \
  MEM_STAT u (x0($1)):(column(b0+o0)/1024/1024/1024):(column(b0+o1)/1024/1024/1024):(column(b0+o2)/1024/1024/1024):(column(b0+o3)/1024/1024/1024) \
    w candlesticks whiskerbars lc rgb C_U lw C_LW not, \
  MEM_STAT u (x0($1)):(column(b0)/1024/1024/1024) w p pt 7 ps PS lc rgb C_U not, \
  MEM_STAT u (x1($1)):(column(b1+o0)/1024/1024/1024):(column(b0+o1)/1024/1024/1024):(column(b0+o2)/1024/1024/1024):(column(b0+o3)/1024/1024/1024) \
    w candlesticks whiskerbars lc rgb C_C lw C_LW not, \
  MEM_STAT u (x1($1)):(column(b1)/1024/1024/1024) w p pt 7 ps PS lc rgb C_C not
}


# Legend for the tail latencies
if (1) {
  reset

  set notics
  set noborder
  set lmargin 0
  set rmargin 0
  set bmargin 0
  set tmargin 0

  LW=2

  if (1) {
    xm=0.08
    bw=0.03
    xl=xm-bw/2
    xr=xm+bw/2
    yt=0.97
    yb=yt-0.45
    y1=yb+(yt-yb)*1/4
    y2=yb+(yt-yb)*3/4

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice (face and border) to erase the vertical line behind the box
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "blue" fc rgb "blue" lw LW front

    yc=(yt+yb)/2
    set obj circle at graph xm,yc size graph .007 fs transparent solid fc rgb "blue" front

    yb1=yb-0.03
    set label "Unmodified" at graph xm,yb1 right rotate by 90 tc rgb "blue" front
  }

  if (1) {
    xm=xm+0.06
    xl=xm-bw/2
    xr=xm+bw/2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "red"

    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "red" fc rgb "red" lw LW front

    set obj circle at graph xm,yc size graph .007 fs transparent solid fc rgb "red" front

    set label "Computation" at graph xm,yb1 right rotate by 90 tc rgb "red" front
  }

  if (1) {
    xm=xm+0.05
    set label "Max" at graph xm,yt left
    set label "75th"  at graph xm,y2 left
    set label "25th"    at graph xm,y1 left
    set label "Min"    at graph xm,yb left
    set label "Avg"     at graph xm,yc left
  }

  f(x)=x
  plot f(x) lc rgb "white" not
}
