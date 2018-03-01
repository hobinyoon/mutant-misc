# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

size_x = 2.9
size_y = size_x * 0.69
set terminal pdfcairo enhanced size (size_x)in, (size_y)in
set output OUT_FN

if (0) {
  # https://www.particleincell.com/2014/colormap/
  # Short rainbow
  # It's nice, but the yellow color is not very visible.
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
} else {
  #c_r(a) = floor(255.999 * a)
  c_r(a) = floor(255.999 * (a < 0.5 ? 2*a : 1))
  c_g(a) = 0
  #c_b(a) = floor(255.999 * (1.0 - a))
  c_b(a) = floor(255.999 * (a < 0.5 ? 1 : 2 - 2*a))
  color_01(a) = c_r(a) * 256 * 256 + c_g(a) * 256 + c_b(a)
}


c_min = 0.045
c_max = 0.528

TMARGIN = 0.96
RMARGIN = 0.71

# Average read latency
if (1) {
  reset
  set xlabel "Throughput (K IOPS)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy
  set xrange[1/1.5:100*1.5]

  # Legend
  if (1) {
    x_l = 0.75
    x_r = x_l + 0.023
    y_t = 0.96
    y_height = 0.745
    y_b = y_t - y_height
    y_c = (y_t + y_b) / 2.0

    # Play with this if you see horizontal stripes
    y_overlap=0.95
    y_unit_height = y_height / 256.0

    do for [i=0:255] {
      set obj rect from screen x_l, y_t - y_unit_height * (i+1+y_overlap) to screen x_r, y_t - y_unit_height * i \
        fs solid 1.0 noborder fc rgb color_01(i / 255.0) lw 0.1 front
    }

    # Bounding box
    set obj rect from screen x_l, y_t - y_unit_height * (255+1+y_overlap) to screen x_r, y_t - y_unit_height * (0) \
      fs transparent solid 0.0 border fc rgb "#808080" front

    # For Mutant, these are cost SLOs, not actual costs.
    # For RocksDB, these are actual costs.
    costs = "0.045 0.1 0.2 0.3 0.4 0.5 0.528"
    cost_min = 0.045
    cost_max = 0.528
    cost_01(x) = (x - cost_min) / (cost_max - cost_min)
    x_r1 = x_r + 0.015
    x_r2 = x_r1 + 0.03
    x_r3 = x_r2 + 0.02
    do for [i=1:words(costs)] {
      #cost_str = sprintf("$%s", word(costs, i))
      cost_str = word(costs, i)
      #print cost_str
      cost = cost_str + 0.0
      y0 = y_t + (y_b - y_t) * cost_01(cost)
      set arrow from screen x_r, y0 to screen x_r1, y0 nohead lc rgb "#808080" front
      set label at screen x_r2, y0 point pt i ps 0.5 lc rgb color_01(cost_01(cost)) front
      set label cost_str at screen x_r3, y0 left tc rgb "black" front
    }

    set label "Cost ($/GB/month)" at screen x_r, y_c center offset 8,0 rotate by 90
  }

  if (1) {
    x0 = 0.24
    y0 = 0.94
    x00 = x0 - 0.060
    x01 = x0 + 0.06
    y00 = y0 - 0.08
    y01 = y0 + 0.035
    set obj rect from screen x00,y00 to screen x01,y01 fs noborder fc rgb "white" front
    set label "Slow\nDB" center at screen x0,y0 front

    x0 = 0.70
    y0 = 0.73
    x00 = x0 - 0.040
    x01 = x0 + 0.04
    y00 = y0 - 0.08
    y01 = y0 + 0.035
    set obj rect from screen x00,y00 to screen x01,y01 fs noborder fc rgb "white" front
    set label "Fast\nDB" center at screen x0,y0 front

    x0 = 0.34
    y0 = 0.78
    x1 = 0.63
    y1 = 0.60
    set arrow from screen x0,y0 to screen x1,y1 heads size screen 0.008,90

    x0 = 0.425
    y0 = 0.78
    x1 = x0 + 0.040
    y1 = y0 - 0.035
    set label "M" at screen x0,y0 rotate by -24 font "Times,16" front
    set label "UTANT" at screen x1,y1 rotate by -24 font "Times,12" front
  }

  set tmargin screen TMARGIN
  set rmargin screen RMARGIN

  color_cost(x) = color_01((x - c_min) / (c_max - c_min))

  LW = 2
  PS = 0.4

  costs = "0.045 0.1 0.2 0.3 0.4 0.5 0.528"

  set ylabel "Read latency (ms)" offset 1.5,0
  # Base index
  b=5

  i = 1
  set yrange[0.05:3]
  plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
}


# Average write latency
if (1) {
  reset
  set xlabel "Throughput (K IOPS)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy
  set xrange[1/1.5:100*1.5]

  set tmargin screen TMARGIN
  set rmargin screen RMARGIN

  color_cost(x) = color_01((x - c_min) / (c_max - c_min))

  LW = 2
  PS = 0.4

  costs = "0.045 0.1 0.2 0.3 0.4 0.5 0.528"

  set ylabel "Write latency (ms)" offset 1.5,0
  # Base index
  b=10

  i = 1
  set yrange[0.01:10]
  plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
}
