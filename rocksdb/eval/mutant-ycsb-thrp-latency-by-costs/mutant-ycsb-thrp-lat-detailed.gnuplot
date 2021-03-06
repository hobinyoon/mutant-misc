# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set terminal pdfcairo enhanced size 2.5in, (2.5*0.85)in
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


# Legend
if (1) {
  x_l = 0.1
  x_r = x_l + 0.04
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
  set obj rect from graph x_l, y_t - y_unit_height * (255+1+y_overlap) to graph x_r, y_t - y_unit_height * (0) \
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
    set label at graph x_r + 0.05, y0 point pt i ps 0.5 lc rgb color_01(cost_01(cost)) front
    set label cost_str at graph x_r, y0 left offset 2.5,0 tc rgb color_01(cost_01(cost)) front
  }

  set label "Cost ($/GB/month)" at graph x_r, y_c center offset 8,0 rotate by 90

  set notics
  set noborder
  plot x lc rgb "white" not
}


c_min = 0.045
c_max = 0.528

if (1) {
  reset
  set xlabel "K IOPS"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy
  set xrange[1/1.5:100*1.5]
  #set yrange[0.1:]

  color_cost(x) = color_01((x - c_min) / (c_max - c_min))

  l_x = 0.97
  l_y = 0.9
  labels = "Average 90th 99th 99.9th 99.99th"

  LW = 2
  PS = 0.4
  RB = 35

  costs = "0.045 0.1 0.2 0.3 0.4 0.5 0.528"

  # Read latency
  if (1) {
    set ylabel "Read latency (ms)" offset 1.5,0
    # Base index
    b=5
    do for [i=1:words(labels)] {
      if (i == 1) {
        unset label 1
        set yrange[0.05:3]
        plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
      } else {
        set label 1 word(labels, i) at graph l_x,l_y right
        set autoscale y
        plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
      }
    }
  }

  # Write latency
  if (1) {
    set autoscale y
    set ylabel "Write latency (ms)" offset 1.5,0
    b = 10
    do for [i=1:words(labels)] {
      if (i == 1) {
        unset label 1
      } else {
        set label 1 word(labels, i) at graph l_x,l_y right
      }
      plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
    }
  }

  # Read latency avg. y-axis linear scale. This might be better to present.
  b = 5
  i = 1
  set ylabel "Read latency (ms)" offset 0.0,0
  #set label 1 word(labels, i) at graph l_x,l_y right
  unset label 1
  unset logscale
  set logscale x
  set yrange[0:1.6]
  set ytics nomirror tc rgb "black" format "%.1f" autofreq 0,0.5
  plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
}


# Unmodified DB performance with tail latencies
if (1) {
  reset
  set xlabel "K IOPS"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy
  set xrange[1/1.5:100*1.5]
  set yrange[:100*1.5]

  color_cost(x) = color_01((x - c_min) / (c_max - c_min))

  LW = 2
  PS = 0.4
  BW = 0.06

  set boxwidth BW

  costs = "0.045 0.528"

  # Read latency
  if (1) {
    set ylabel "Read latency (ms)" offset 1.5,0

    # Base index
    b=5

    plot \
      for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000):(color_cost($1)) w candlesticks lc rgb variable lw LW fillstyle empty not whiskerbars, \
      for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b)/1000):(color_cost($1)) w lp pt 7 ps PS lc rgb variable lt 0 lw LW not
  }

  # Write latency
  if (1) {
    #set autoscale y
    set ylabel "Write latency (ms)" offset 1.5,0
    b = 10
    plot \
      for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000):(color_cost($1)) w candlesticks lc rgb variable lw LW fillstyle empty not whiskerbars, \
      for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b)/1000):(color_cost($1)) w lp pt 7 ps PS lc rgb variable lt 0 lw LW not

    #plot for [j=1:words(costs)] IN_YCSB u ($1 == word(costs, j) ? $4/1000 : 1/0):(column(b + i - 1)/1000):(color_cost($1)) w lp pt j ps PS lc rgb variable lw LW not
  }
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
    yt=0.95
    yb=yt-0.25
    y1=yb+(yt-yb)*1/3
    y2=yb+(yt-yb)*2/3

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice (face and border) to erase the vertical line behind the box
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "blue" fc rgb "blue" lw LW front

    yb1=yb-0.10
    set obj circle at graph xm,yb1 size graph .007 fs transparent solid fc rgb "blue" front

    yb2=yb1-0.12
    set label "$0.045\nEBS\nMag" at graph xm,yb2 center tc rgb "blue"
  }

  if (1) {
    xm=xm+0.20
    xl=xm-bw/2
    xr=xm+bw/2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "red"

    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "red" fc rgb "red" lw LW front

    set obj circle at graph xm,yb1 size graph .007 fs transparent solid fc rgb "red" front

    set label "$0.528\nLocal\nSSD" at graph xm,yb2 center tc rgb "red"
  }

  if (1) {
    xm=xm+0.10
    set label "99.99th" at graph xm,yt left
    set label "99.9th"  at graph xm,y2 left
    set label "99th"    at graph xm,y1 left
    set label "90th"    at graph xm,yb left
    set label "Avg"     at graph xm,yb1 left
  }

  f(x)=x
  plot f(x) lc rgb "white" not
}
