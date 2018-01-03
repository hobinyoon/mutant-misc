# Tested with gnuplot 4.6 patchlevel 6

PARAMS = system("echo $PARAMS")
TIME_MAX = system("echo $TIME_MAX")
NUM_STG_DEVS = system("echo $NUM_STG_DEVS") + 0
IN_FN_DSTAT = system("echo $IN_FN_DSTAT")
IN_FN_YCSB = system("echo $IN_FN_YCSB")
IN_FN_ROCKSDB = system("echo $IN_FN_ROCKSDB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

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
  plot f(x) lc rgb "#F0F0F0" not
}

LMARGIN = 10
set sample 1000

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
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  if (NUM_STG_DEVS == 3) {
    i_x=21
    i_y=14
  } else {
    print(sprintf("Unexpected %s", NUM_STG_DEVS))
    exit
  }

  plot IN_FN_DSTAT u (column(i_x)):(column(i_y)/1048576) w lp pt 7 ps 0.08 lc rgb "red" not
}


# Disk IOs in MiB
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Read, Write (MiB/sec)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  if (NUM_STG_DEVS == 3) {
    i_x = 21
    i_y = 3
  } else {
    print(sprintf("Unexpected %s", NUM_STG_DEVS))
    exit
  }

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


# Disk IOs in IOPS
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "Read, Write (IOPS)" offset 1,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]

  if (NUM_STG_DEVS == 3) {
    i_x = 21
    i_y = 9
  } else {
    print(sprintf("Unexpected %s", NUM_STG_DEVS))
    exit
  }

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


# DB IOPS breakdown into reads and writes?  We'll see if it's needed. When you specify target IOPS, it's not needed.


# Total number of SSTables
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "SSTables created"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:]

  set boxwidth "00:00:01"
  plot \
  IN_FN_ROCKSDB u 1:2 w boxes lc rgb "blue" not
}


# Number of SSTables created either from flush or compaction
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "SSTables created"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:]

  set boxwidth "00:00:01"
  plot \
  IN_FN_ROCKSDB u 1:2 w boxes lc rgb "blue" not
}


# Total sizes of of SSTables created either from flush or compaction
if (0) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%H:%M"

  set xlabel "Time (HH:MM)"
  set ylabel "SSTables created (MiB)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Align the stacked plots
  set lmargin LMARGIN

  set xrange ["00:00:00":TIME_MAX]
  set yrange [0:]

  set boxwidth "00:00:01"
  plot \
  IN_FN_ROCKSDB u 1:($3/1048576) w boxes lc rgb "blue" not
  #IN_FN_ROCKSDB u 1:($3/1048576) w p pt 7 ps 0.15 lc rgb "blue" not
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
  set yrange [0:100]

  if (NUM_STG_DEVS == 3) {
    i_x = 21
    i_y = 23
  } else {
    print(sprintf("Unexpected %s", NUM_STG_DEVS))
    exit
  }

  # CPU: sys, user, iowait
  plot \
  IN_FN_DSTAT u i_x:(column(i_y + 2)) w p pt 7 ps 0.15 lc rgb "#FF8080" not, \
  IN_FN_DSTAT u i_x:(column(i_y + 3)) w p pt 7 ps 0.15 lc rgb "#8080FF" not, \
  IN_FN_DSTAT u i_x:(column(i_y + 4)) w p pt 7 ps 0.15 lc rgb "#808080" not, \
  IN_FN_DSTAT u i_x:(100 - column(i_y)) w p pt 7 ps 0.15 lc rgb "#FF0000" not, \

  #IN_FN_DSTAT u i_x:(100 - column(i_y)) w l smooth bezier lw 3 lc rgb "blue" not
}

# exit
