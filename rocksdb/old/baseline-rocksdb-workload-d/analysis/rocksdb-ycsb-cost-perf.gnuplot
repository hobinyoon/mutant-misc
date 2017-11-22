# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output OUT_FN

LMARGIN = 8

if (1) {
  reset
  set xlabel "Cost ($/GB/month)"
  set ylabel "Read latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Legend
  if (1) {
    xm=0.9
    bw=0.04
    xl=xm-bw/2
    xr=xm+bw/2
    yt=0.95
    yb=yt-0.25
    y1=yb+(yt-yb)*1/3
    y2=yb+(yt-yb)*2/3

    LW=2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "blue" lw LW front

    x1=xl-0.04
    set label "99.99th" at graph x1,yt right font ",10"
    set label "99.9th"  at graph x1,y2 right font ",10"
    set label "99th"    at graph x1,y1 right font ",10"
    set label "90th"    at graph x1,yb right font ",10"

    yb1=yb-0.08
    set obj circle at graph xm,yb1 size graph .013 fs solid fc rgb "red" front
    set label "Avg"     at graph x1,yb1 right font ",10"
  }

  set boxwidth 0.02

  # Align the stacked plots
  set lmargin LMARGIN

  bi=9
  plot \
  IN_YCSB u 2:(column(bi)/1000) w p pt 7 ps 0.4 not, \
  IN_YCSB u 2:(column(bi+4)/1000):(column(bi+3)/1000):(column(bi+6)/1000):(column(bi+5)/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not

  # x  box_min  whisker_min  whisker_high  box_high
}

# Logscale y
if (1) {
  reset
  set xlabel "Cost ($/GB/month)"
  set ylabel "Read latency (ms)" offset 2,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Legend
  if (1) {
    xm=0.9
    bw=0.04
    xl=xm-bw/2
    xr=xm+bw/2
    yt=0.95
    yb=yt-0.25
    y1=yb+(yt-yb)*1/3
    y2=yb+(yt-yb)*2/3

    LW=2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "blue" lw LW front

    x1=xl-0.04
    set label "99.99th" at graph x1,yt right font ",10"
    set label "99.9th"  at graph x1,y2 right font ",10"
    set label "99th"    at graph x1,y1 right font ",10"
    set label "90th"    at graph x1,yb right font ",10"

    yb1=yb-0.08
    set obj circle at graph xm,yb1 size graph .013 fs solid fc rgb "red" front
    set label "Avg"     at graph x1,yb1 right font ",10"
  }

  set boxwidth 0.02
  set lmargin LMARGIN

  set logscale y
  bi=9
  plot \
  IN_YCSB u 2:(column(bi)/1000) w p pt 7 ps 0.4 not, \
  IN_YCSB u 2:(column(bi+4)/1000):(column(bi+3)/1000):(column(bi+6)/1000):(column(bi+5)/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not
}

# Write latency
if (1) {
  reset
  set xlabel "Cost ($/GB/month)"
  set ylabel "Write latency (ms)" offset 1,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # Legend
  if (1) {
    xm=0.9
    bw=0.04
    xl=xm-bw/2
    xr=xm+bw/2
    yt=0.95
    yb=yt-0.25
    y1=yb+(yt-yb)*1/3
    y2=yb+(yt-yb)*2/3

    LW=2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs empty border lc rgb "blue" lw LW front

    x1=xl-0.04
    set label "99.99th" at graph x1,yt right font ",10"
    set label "99.9th"  at graph x1,y2 right font ",10"
    set label "99th"    at graph x1,y1 right font ",10"
    set label "90th"    at graph x1,yb right font ",10"

    yb1=yb-0.08
    set obj circle at graph xm,yb1 size graph .013 fs solid fc rgb "red" front
    set label "Avg"     at graph x1,yb1 right font ",10"
  }

  set boxwidth 0.02
  set lmargin LMARGIN

  set logscale y
  #bi=4
  bi=16
  plot \
  IN_YCSB u 2:(column(bi)/1000) w p pt 7 ps 0.4 not, \
  IN_YCSB u 2:(column(bi+4)/1000):(column(bi+3)/1000):(column(bi+6)/1000):(column(bi+5)/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not
}

if (1) {
  reset
  set xlabel "Cost ($/GB/month)"
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  logscale_y = 1
  if (logscale_y == 0) {
    set yrange[0:]
    set ylabel "DB IOPS (K)" offset 0,0
  } else {
    set logscale y
    set ylabel "DB IOPS (K)" offset 1.5,0
  }

  # Legend
  if (1) {
    if (logscale_y == 0) {
      xm=0.08
      yt=0.95
    } else {
      xm=0.63
      yt=0.39
    }

    bw=0.035
    xl=xm-bw/2
    xr=xm+bw/2
    yb=yt-0.25
    y1=yb+(yt-yb)*1/4
    y2=yb+(yt-yb)*2/4
    y3=yb+(yt-yb)*3/4

    LW=2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y3 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y3 fs empty border lc rgb "blue" lw LW front

    set arrow from graph xl,y2 to graph xr,y2 nohead lw LW lc rgb "blue" front

    x1=xr+0.04
    set label "Max"       at graph x1,yt font ",10"
    set label "Quartiles" at graph x1,y2 font ",10"
    set label "Min"       at graph x1,yb font ",10"

    yb1=yb-0.08
    set obj circle at graph xm,yb1 size graph .013 fs solid fc rgb "red" front
    set label "Avg"     at graph x1,yb1 font ",10"
  }

  set lmargin LMARGIN

  set boxwidth 0.02

  plot \
  IN_YCSB u 2:($6/1000):($4/1000):($5/1000):($8/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  IN_YCSB u 2:($7/1000):($7/1000):($7/1000):($7/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  IN_YCSB u 2:($3/1000) w p pt 7 ps 0.3 lc rgb "red" not
}
