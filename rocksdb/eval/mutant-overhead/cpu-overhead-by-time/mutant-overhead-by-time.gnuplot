# Tested with gnuplot 4.6 patchlevel 6

TIME_MAX = system("echo $TIME_MAX")
CPU_STAT = system("echo $CPU_STAT")
ROCKSDB = system("echo $ROCKSDB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 3.5in, (2.3*0.85)in
set output OUT_FN

# Time vs. CPU usage and the total number of SSTables
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)"
  set ylabel "CPU usage (%)" offset 1,0
  set y2label "# of SSTables" tc rgb "black"
  set xtics nomirror tc rgb "black" #autofreq 0,2*3600
  set ytics nomirror tc rgb "black"
  set y2tics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange ["00:00:00.000":TIME_MAX]
  set yrange [0:100]

  #C_NUM_SSTS = "#8080FF"
  C_NUM_SSTS = "#808080"
  LW_NUM_SSTS = 2

  #C_U = "#808080"
  #C_U = "black"
  C_U = "blue"
  C_C = "red"

  # CPU usage line width
  C_LW = 3

  # Base indices of columes without and wit CPU
  b0 = 2
  b1 = 10

  # x offset in minutes
  x_offset = 9
  x0(a) = sprintf("%02d:%02d:00", a, 30 - x_offset)
  x1(a) = sprintf("%02d:%02d:00", a, 30 + x_offset)

  set boxwidth 13 * 60
  PS = 0.4
  
  plot \
  ROCKSDB u 1:4:3:(0)       w vectors axes x1y2 nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  ROCKSDB u 2:4:(0):($5-$4) w vectors axes x1y2 nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  CPU_STAT u (x0($1)):(column(b0+3)):(column(b0+2)):(column(b0+6)):(column(b0+5)) w candlesticks whiskerbars lc rgb C_U lw C_LW not, \
  CPU_STAT u (x0($1)):(column(b0)) w p pt 7 ps PS lc rgb C_U not, \
  CPU_STAT u (x1($1)):(column(b1+3)):(column(b1+2)):(column(b1+6)):(column(b1+5)) w candlesticks whiskerbars lc rgb C_C lw C_LW not, \
  CPU_STAT u (x1($1)):(column(b1)) w p pt 7 ps PS lc rgb C_C not

  # vectors: x y xdelta ydelta
  # candlesticks: x box_min whisker_min whisker_high box_high
}
