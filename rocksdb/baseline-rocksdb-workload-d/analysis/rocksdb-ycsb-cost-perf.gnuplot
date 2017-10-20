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
  set ylabel "Latency (ms)" offset 1,0
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

    x1=xl-0.06
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

  plot \
  IN_YCSB u 2:($3/1000) w p pt 7 ps 0.4 not, \
  IN_YCSB u 2:($7/1000):($6/1000):($9/1000):($8/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not

  # x  box_min  whisker_min  whisker_high  box_high
}

# Logscale y
if (1) {
  reset
  set xlabel "Cost ($/GB/month)"
  set ylabel "Latency (ms)" offset 2,0
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

    x1=xl-0.06
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
  plot \
  IN_YCSB u 2:($3/1000) w p pt 7 ps 0.4 not, \
  IN_YCSB u 2:($7/1000):($6/1000):($9/1000):($8/1000) w candlesticks whiskerbars lw 2 lc rgb "blue" not
}
