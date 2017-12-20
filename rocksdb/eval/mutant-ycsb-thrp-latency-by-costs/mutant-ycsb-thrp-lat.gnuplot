# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set terminal pdfcairo enhanced size 2.5in, (2.5*0.85)in
set output OUT_FN

BW=0.04
LW=2
PS=0.4
# Fill transparency
F_TP=0.4
CR=0.005

# TODO: Legend
if (1) {
}


# Read latency
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "Read latency (ms)" offset 1.5,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set boxwidth BW
  set style circle radius screen CR

  set logscale xy
  #set logscale x
  set xrange[0.8:150]

  # 0.1 - 0.5
  c_min = 0.045
  c_max = 0.528
  c_margin = 0.1
  c_01(a) = (a - c_min) / c_max
  c_01_m(a) = (a - c_min) / c_max * (1 - c_margin) + c_margin / 2
  c_r(a) = floor(255.999 * c_01_m(a))
  c_g(a) = 0
  c_b(a) = floor(255.999 * (1.0 - c_01_m(a)))
  color(a) = c_r(a) * 256 * 256 + c_g(a) * 256 + c_b(a)

  l_x = 0.97
  l_y = 0.9
  labels = "Average 90th 99th 99.9th 99.99th"

  RB = 35

  # Base index
  b=5

  do for [i=1:words(labels)] {
    if (i == 1) {
      set yrange[0.05:3]
      #set yrange[0:3]
    } else {
      set autoscale y
    }
    set label 1 word(labels, i) at graph l_x,l_y right
    plot \
    IN_YCSB u ($4/1000):(column(b + i - 1)/1000):2:(color($1)) w labels left offset 0.5,0.5 rotate by RB tc rgb variable not, \
    IN_YCSB u ($4/1000):(column(b + i - 1)/1000):(color($1)) w lp pt 6 ps PS lc rgb variable lw LW not
  }

  set autoscale y
  set ylabel "Write latency (ms)" offset 1.5,0
  b = 10
  do for [i=1:words(labels)] {
    set label 1 word(labels, i) at graph l_x,l_y right
    plot \
    IN_YCSB u ($4/1000):(column(b + i - 1)/1000):2:(color($1)) w labels left offset 0.5,0.5 rotate by RB tc rgb variable not, \
    IN_YCSB u ($4/1000):(column(b + i - 1)/1000):(color($1)) w lp pt 6 ps PS lc rgb variable lw LW not
  }
}
