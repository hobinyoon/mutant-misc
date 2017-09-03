# Tested with gnuplot 4.6 patchlevel 6

IN_FN_QZ = system("echo $IN_FN_QZ")
IN_FN_DS = system("echo $IN_FN_DS")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

# Read latency
if (1) {
  set xdata time
  # 00:00:00.491
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "Read latency (ms)" tc rgb "black"

  set yrange[0:50]

  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  plot \
  IN_FN_QZ u 1:($30/1000) w p pt 7 ps 0.2 lc rgb "#FFB0B0" not, \
  IN_FN_QZ u 1:($30/1000) w l smooth bezier lw 6 lc rgb "red" not
}

# Number of reads and writes
if (1) {
  reset
  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set ylabel "Reads/0.5 sec" tc rgb "black"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black" #autofreq 0, 500
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set logscale y

  plot \
  IN_FN_QZ u 1:29 w p pt 7 ps 0.2 lc rgb "blue" t "read", \
  IN_FN_QZ u 1:8  w p pt 7 ps 0.2 lc rgb "red" t "write"
}

# EBS st1 disk IOs
if (1) {
  reset

  set border front lc rgb "#808080" back
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border front lc rgb "#808080" back

  set xdata time
  set timefmt "%H:%M:%S"
  set format x "%M"

  set xlabel "Time (minute)"
  set ylabel "EBS Mag IOPS"
  unset y2label

  set logscale y

  plot \
  IN_FN_DS u 25:15 w p pt 7 ps 0.2 lc rgb "blue" t "read", \
  IN_FN_DS u 25:16 w p pt 7 ps 0.2 lc rgb "red" t "write"
}
