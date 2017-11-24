# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 3.6in, (2.3*0.85)in
set output OUT_FN

# Read latency
if (1) {
  set xlabel "K IOPS"
  set ylabel "Read latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy
  #set logscale y

  set xrange[0.8:200]
  set yrange[0.01:200]

  set boxwidth 0.06

  LW=2
  PS=0.4

  # Base index
  b=4

  plot \
  IN_YCSB u (strcol(1) eq "ebs-st1" ? ($3/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW not whiskerbars, \
  IN_YCSB u (strcol(1) eq "ebs-st1" ? ($3/1000) : 1/0) \
    :(column(b)/1000) w p pt 7 ps PS lc rgb "blue" not, \
  IN_YCSB u (strcol(1) eq "local-ssd" ? ($3/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW not whiskerbars, \
  IN_YCSB u (strcol(1) eq "local-ssd" ? ($3/1000) : 1/0) \
    :(column(b)/1000) w p pt 7 ps PS lc rgb "red" not, \

  # whisker plot: x box_min whisker_min whisker_high box_high
  #            iops      99          90        99.99     99.9
  #               3       6           5            8        7
  #               3     5+1         5+0          5+3      5+2
}


# Write latency
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "Write latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy

  set xrange[0.8:200]
  set yrange[0.01:200]

  set boxwidth 0.06

  LW=2
  PS=0.4

  # Base index
  b=9

  plot \
  IN_YCSB u (strcol(1) eq "ebs-st1" ? ($3/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW not whiskerbars, \
  IN_YCSB u (strcol(1) eq "ebs-st1" ? ($3/1000) : 1/0) \
    :(column(b)/1000) w p pt 7 ps PS lc rgb "blue" not, \
  IN_YCSB u (strcol(1) eq "local-ssd" ? ($3/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW not whiskerbars, \
  IN_YCSB u (strcol(1) eq "local-ssd" ? ($3/1000) : 1/0) \
    :(column(b)/1000) w p pt 7 ps PS lc rgb "red" not, \
}


# Legend
if (1) {
  reset

  set notics
  set noborder
  set lmargin 0
  set rmargin 0
  set bmargin 0
  set tmargin 0

  xm=0.17
  bw=0.025
  xl=xm-bw/2
  xr=xm+bw/2
  yt=0.95
  yb=yt-0.35
  y1=yb+(yt-yb)*1/3
  y2=yb+(yt-yb)*2/3

  LW=2

  set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "black"
  set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "black"
  set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "black"

  # Draw the box twice: face and border
  set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
  set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "black" lw LW front

  x1=xl-0.03
  set label "99.99th" at graph x1,yt right #font ",10"
  set label "99.9th"  at graph x1,y2 right #font ",10"
  set label "99th"    at graph x1,y1 right #font ",10"
  set label "90th"    at graph x1,yb right #font ",10"

  yb1=yb-0.12
  set obj circle at graph xm,yb1 size graph .007 fs solid fc rgb "black" front
  set label "Avg"     at graph x1,yb1 right #font ",10"

  f(x)=x
  plot f(x) lc rgb "white" not
}
