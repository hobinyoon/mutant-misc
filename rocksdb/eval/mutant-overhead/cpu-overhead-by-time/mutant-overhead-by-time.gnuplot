# Tested with gnuplot 4.6 patchlevel 6

TIME_MAX = system("echo $TIME_MAX")
CPU_STAT = system("echo $CPU_STAT")
MEM_STAT = system("echo $MEM_STAT")
ROCKSDB = system("echo $ROCKSDB")
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
  ROCKSDB u 1:4:3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  ROCKSDB u 2:4:(0):($5-$4) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

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
