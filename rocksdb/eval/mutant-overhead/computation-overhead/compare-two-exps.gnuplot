# Tested with gnuplot 4.6 patchlevel 6

TIME_MAX = system("echo $TIME_MAX")
FN_ROCKSDB = system("echo $FN_ROCKSDB")
FN_CPU_1MIN_AVG = system("echo $FN_CPU_1MIN_AVG")
FN_MEM_1MIN_AVG = system("echo $FN_MEM_1MIN_AVG")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)
#print sprintf("FN_MEM_1MIN_AVG=%s", FN_MEM_1MIN_AVG)

set terminal pdfcairo enhanced size 3.6in, (3.5*0.35)in
set output OUT_FN

LMARGIN = 0.14
RMARGIN = 0.99
TMARGIN = 0.95

# Time vs. 1-min CPU average
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  #set xlabel "Time (hour)" offset 0,0.2
  set ylabel "CPU (%)" offset 1,0
  set xtics nomirror tc rgb "white"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:100]

  PS = 0.1

  # Blue and red
  c0(a) = (a == 0 ? 255 : 255 * 256 * 256)

  if (1) {
    # Plotting of the two symbols in the order of timestamp to prevent one type is always in front of the other type.
    #   https://stackoverflow.com/questions/29622885/how-set-point-type-from-data-in-gnuplot
    set encoding utf8
    symbol(a) = "+x"[int(a+1):int(a+1)]

    # Legends
    if (1) {
      x0 = 0.05
      y0 = 0.86
      set label symbol(0) at graph x0, y0 center tc rgb c0(0) font ",12" front
      x1 = x0 + 0.03
      set label "Unmodified DB" at graph x1, y0 left tc rgb c0(0) font ",12" front
      y1 = y0 - 0.15
      set label symbol(1) at graph x0, y1 center tc rgb c0(1) font ",12" front
      set label "With computation" at graph x1, y1 left tc rgb c0(1) font ",12" front
    }

    plot FN_CPU_1MIN_AVG u 1:2:(symbol($3)):(c0($3)) w labels tc rgb variable font ",6" not
  } else {
    plot FN_CPU_1MIN_AVG u 1:2:(c0($3)) w p pt 7 ps PS lc rgb variable not
  }
}


# Time vs. 1-min memory usage average
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  #set xlabel "Time (hour)" offset 0,0.2
  set ylabel "Memory (GB)" #offset 0.5,0
  set xtics nomirror tc rgb "white"
  set ytics nomirror tc rgb "black" format "%.1f" autofreq 0,0.5,2.4
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:2.5]

  PS = 0.1

  # Blue and red
  c0(a) = (a == 0 ? 255 : 255 * 256 * 256)

  if (1) {
    # Plotting of the two symbols in the order of timestamp to prevent one type is always in front of the other type.
    #   https://stackoverflow.com/questions/29622885/how-set-point-type-from-data-in-gnuplot
    set encoding utf8
    symbol(a) = "+x"[int(a+1):int(a+1)]

    # Legends
    if (1) {
      #x0 = 0.05
      #y0 = 0.86
      x0 = 0.52
      y0 = 0.32
      set label symbol(0) at graph x0, y0 center tc rgb c0(0) font ",12" front
      x1 = x0 + 0.03
      set label "Unmodified DB" at graph x1, y0 left tc rgb c0(0) font ",12" front
      y1 = y0 - 0.15
      set label symbol(1) at graph x0, y1 center tc rgb c0(1) font ",12" front
      set label "With computation" at graph x1, y1 left tc rgb c0(1) font ",12" front
    }

    plot FN_MEM_1MIN_AVG u 1:2:(symbol($3)):(c0($3)) w labels tc rgb variable font ",6" not
  } else {
    plot FN_MEM_1MIN_AVG u 1:2:(c0($3)) w p pt 7 ps PS lc rgb variable not
  }
}


# Time vs. total number of SSTables
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  set ylabel "# of SSTables" offset 1, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" autofreq 0,100,390
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set xrange ["00:00:00.000":TIME_MAX]
  set yrange [0:400]

  C_NUM_SSTS = "red"
  LW_NUM_SSTS = 2

  plot \
  FN_ROCKSDB u 1:($4+$5):3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  FN_ROCKSDB u 2:($4+$5):(0):($6+$7-$4-$5) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

  # vectors: x y xdelta ydelta
}

# Time vs. total SSTable size
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%1H"

  set xlabel "Time (hour)" offset 0,0.2
  #set ylabel "Total SSTable size\n(GB)" offset 0.5, 0
  set ylabel "SSTable size (GB)" #offset 0.2, 0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" autofreq 0,5
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set xrange ["00:00:00.000":TIME_MAX]

  C_NUM_SSTS = "red"
  LW_NUM_SSTS = 2

  plot \
  FN_ROCKSDB u 1:($8+$9):3:(0)       w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not, \
  FN_ROCKSDB u 2:($8+$9):(0):($10+$11-$8-$9) w vectors nohead lc rgb C_NUM_SSTS lw LW_NUM_SSTS not

  # vectors: x y xdelta ydelta
}
