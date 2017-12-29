# Tested with gnuplot 4.6 patchlevel 6

IN_YCSB = system("echo $IN_YCSB")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 3.3in, (2.3*0.85)in
set output OUT_FN

BW=0.04
LW=2
PS=0.5
# Fill transparency
F_TP=0.4
CR=0.005

# Read latency
if (1) {
  set xlabel "K IOPS"
  set ylabel "Read latency (ms)" offset 1.5,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set yrange[0.01:]

  set boxwidth BW
  set style circle radius screen CR

  # Base index
  b=5

  if (0) {
    # x-axis true to the scale
    set logscale y
    plot \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? $0 : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000):xticlabel(4) w candlesticks lc rgb "blue" lw LW fillstyle solid not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? $0 : 1/0):(column(b)/1000) w p pt 7 ps PS lc rgb "blue" not, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? $0 : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? $0 : 1/0):(column(b)/1000) w p pt 6 ps PS lc rgb "blue" not, \
    \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? $0 : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW fillstyle solid not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? $0 : 1/0):(column(b)/1000) w p pt 7 ps PS lc rgb "red" not, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? $0 : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? $0 : 1/0):(column(b)/1000) w p pt 6 ps PS lc rgb "red" not

  } else {
    set logscale xy
    set xrange[0.8:150]
    plot \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? ($4/1000) : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW fillstyle transparent solid F_TP not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "blue" fillstyle transparent solid F_TP not, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? ($4/1000) : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "blue" fillstyle transparent solid 0 not, \
    \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? ($4/1000) : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW fillstyle transparent solid F_TP not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "red" fillstyle transparent solid F_TP not, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? ($4/1000) : 1/0) \
      :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW not whiskerbars, \
    IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "red" fillstyle transparent solid 0 not, \
  }

  # whisker plot: x box_min whisker_min whisker_high box_high
  #            iops      99          90        99.99     99.9
  #               3       6           5            8        7
  #               3     5+1         5+0          5+3      5+2
}


# Write latency
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "Write latency (ms)" offset 1.5,0
  set xtics nomirror tc rgb "black"
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set logscale xy

  set xrange[0.8:150]
  set yrange[0.01:200]

  set boxwidth BW
  set style circle radius screen CR

  # Base index
  b=10

  plot \
  IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? ($4/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW fillstyle transparent solid F_TP not whiskerbars, \
  IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 0) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "blue" fillstyle transparent solid F_TP not, \
  IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? ($4/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "blue" lw LW not whiskerbars, \
  IN_YCSB u ((strcol(1) eq "ebs-st1") && (strcol(3) == 1) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "blue" fillstyle transparent solid 0 not, \
  \
  IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? ($4/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW fillstyle transparent solid F_TP not whiskerbars, \
  IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 0) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "red" fillstyle transparent solid F_TP not, \
  IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? ($4/1000) : 1/0) \
    :(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) w candlesticks lc rgb "red" lw LW not whiskerbars, \
  IN_YCSB u ((strcol(1) eq "local-ssd") && (strcol(3) == 1) ? ($4/1000) : 1/0):(column(b)/1000) w circles lc rgb "red" fillstyle transparent solid 0 not, \

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

  LW=2

  if (1) {
    xm=0.04
    bw=0.025
    xl=xm-bw/2
    xr=xm+bw/2
    yt=0.95
    yb=yt-0.35
    y1=yb+(yt-yb)*1/3
    y2=yb+(yt-yb)*2/3

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "blue"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "blue"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs transparent solid 0.3 border lc rgb "blue" fc rgb "blue" lw LW front

    yb1=yb-0.12
    set obj circle at graph xm,yb1 size graph .007 fs transparent solid 0.3 fc rgb "blue" front

    yb2=yb1-0.12
    set label "EBS\nMag" at graph xm,yb2 center tc rgb "blue"
  }

  if (1) {
    xm=xm+0.1
    xl=xm-bw/2
    xr=xm+bw/2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "red"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "red"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs transparent solid 0.3 border lc rgb "red" fc rgb "red" lw LW front

    set obj circle at graph xm,yb1 size graph .007 fs transparent solid 0.3 fc rgb "red" front

    set label "Local\nSSD" at graph xm,yb2 center tc rgb "red"
  }

  if (1) {
    xm=xm+0.1
    xl=xm-bw/2
    xr=xm+bw/2

    set arrow from graph xm,yb to graph xm,yt nohead lw LW lc rgb "black"
    set arrow from graph xl,yt to graph xr,yt nohead lw LW lc rgb "black"
    set arrow from graph xl,yb to graph xr,yb nohead lw LW lc rgb "black"

    # Draw the box twice: face and border
    set obj rect from graph xl,y1 to graph xr,y2 fs solid noborder fc rgb "white" front
    set obj rect from graph xl,y1 to graph xr,y2 fs transparent solid 0 border lc rgb "black" fc rgb "black" lw LW front

    set obj circle at graph xm,yb1 size graph .007 fs transparent solid 0 fc rgb "black" front

    x1=xl+0.07
    set label "99.99th" at graph x1,yt left
    set label "99.9th"  at graph x1,y2 left
    set label "99th"    at graph x1,y1 left
    set label "90th"    at graph x1,yb left
    set label "Avg"     at graph x1,yb1 left

    set label "Unsustainable\nthroughput\n(Empty fill)" at graph xm,yb2 left offset -1,0 tc rgb "black"
    # Or "System saturated"
  }

  f(x)=x
  plot f(x) lc rgb "white" not
}
