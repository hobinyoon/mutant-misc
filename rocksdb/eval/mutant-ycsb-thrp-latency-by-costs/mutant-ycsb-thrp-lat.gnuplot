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

# https://www.particleincell.com/2014/colormap/
# Short rainbow
c_a(x) = (1-x)/0.25
c_x(x) = floor(c_a(x))
c_y(x) = floor(255.999 * (c_a(x)-c_x(x)))
c_r(x) = \
  c_x(x) == 0 ? 255          : ( \
  c_x(x) == 1 ? 255 - c_y(x) : ( \
  c_x(x) == 2 ? 0            : ( \
  c_x(x) == 3 ? 0            : ( \
  0 ))))
c_g(x) = \
  c_x(x) == 0 ? c_y(x)       : ( \
  c_x(x) == 1 ? 255          : ( \
  c_x(x) == 2 ? 255          : ( \
  c_x(x) == 3 ? 255 - c_y(x) : ( \
  0 ))))
c_b(x) = \
  c_x(x) == 0 ? 0      : ( \
  c_x(x) == 1 ? 0      : ( \
  c_x(x) == 2 ? c_y(x) : ( \
  c_x(x) == 3 ? 255    : ( \
  255 ))))
color_01(a) = c_r(a) * 256 * 256 + c_g(a) * 256 + c_b(a)


# Legend
if (1) {
  x_l = 0.1
  x_r = x_l + 0.05
  y_t = 0.9
  y_height = 0.8
  y_b = y_t - y_height
  y_c = (y_t + y_b) / 2.0

  # Play with this if you see horizontal stripes
  y_overlap=0.95
  y_unit_height = y_height / 256.0

  do for [i=0:255] {
    set obj rect from graph x_l, y_t - y_unit_height * (i+1+y_overlap) to graph x_r, y_t - y_unit_height * i \
      fs solid 1.0 noborder fc rgb color_01(i / 255.0) lw 0.1 front
  }

  # Bounding box
  set object rect from graph x_l, y_t - y_unit_height * (255+1+y_overlap) to graph x_r, y_t - y_unit_height * (0) \
    fs transparent solid 0.0 border fc rgb "#808080" front

  # For Mutant, these are cost SLOs, not actual costs.
  # For RocksDB, these are actual costs.
  costs = "0.045 0.1 0.2 0.3 0.4 0.5 0.528"
  cost_min = 0.045
  cost_max = 0.528
  cost_01(x) = (x - cost_min) / (cost_max - cost_min)
  do for [i=1:words(costs)] {
    #cost_str = sprintf("$%s", word(costs, i))
    cost_str = word(costs, i)
    cost = word(costs, i) + 0.0
    y0 = y_t + (y_b - y_t) * cost_01(cost)
    set arrow from graph x_r, y0 to graph x_r+0.02, y0 nohead lc rgb "#808080" front
    # Cost label to black. If you do variable color, yellow is not very visible.
    #set label cost_str at graph x_r, y0 left offset 1,0 tc rgb color_01(cost_01(cost)) front
    set label cost_str at graph x_r, y0 left offset 1,0 tc rgb "black" front
  }

  set label "Cost ($/GB/month)" at graph x_r, y_c center offset 7,0 rotate by 90

  set notics
  set noborder
  plot x lc rgb "white" not
}


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
  color_cost(x) = color_01((x - c_min) / (c_max - c_min))

  # TODO: clean up
  if (0) {
    c_margin = 0.1
    c_01(a) = (a - c_min) / (c_max - c_min)
    c_01_m(a) = (a - c_min) / (c_max - c_min) * (1 - c_margin) + c_margin / 2
    c_r(a) = floor(255.999 * c_01_m(a))
    c_g(a) = 0
    c_b(a) = floor(255.999 * (1.0 - c_01_m(a)))
    color(a) = c_r(a) * 256 * 256 + c_g(a) * 256 + c_b(a)
  }

  l_x = 0.97
  l_y = 0.9
  labels = "Average 90th 99th 99.9th 99.99th"

  RB = 35

  # Read latency
  if (1) {
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
      IN_YCSB u ($4/1000):(column(b + i - 1)/1000):(color_cost($1)) w lp pt 6 ps PS lc rgb variable lw LW not
      #IN_YCSB u ($4/1000):(column(b + i - 1)/1000):2:(color_cost($1)) w labels left offset 0.5,0.5 rotate by RB tc rgb variable not
    }
  }

  # Write latency
  if (1) {
    set autoscale y
    set ylabel "Write latency (ms)" offset 1.5,0
    b = 10
    do for [i=1:words(labels)] {
      set label 1 word(labels, i) at graph l_x,l_y right
      plot \
      IN_YCSB u ($4/1000):(column(b + i - 1)/1000):(color_cost($1)) w lp pt 6 ps PS lc rgb variable lw LW not
      #IN_YCSB u ($4/1000):(column(b + i - 1)/1000):2:(color_cost($1)) w labels left offset 0.5,0.5 rotate by RB tc rgb variable not
    }
  }
}
