# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

if (1) {
  reset

  set xlabel "Cost ($/GB/month)"
  set ylabel "Latency (ms)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  #set logscale xy

  plot \
  IN_YCSB u 2:($3/1000) w p pt 7 t "avg"

  #IN_YCSB u 2:3 w p pt 7 ps 0.05 lc rgb "red" not
}
