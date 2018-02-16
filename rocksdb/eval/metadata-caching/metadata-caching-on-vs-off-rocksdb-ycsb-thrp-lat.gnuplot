#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 6

IN_W_O_WO_LAT = "data/with-over-wo"
IN_W = "data/with-metadata-caching"
IN_WO = "data/wo-metadata-caching"
IN_W_O_WO_MEM = "data/memory-usage"
OUT_FN = "metadata-caching-on-vs-off-rocksdb-ycsbd-thrp-vs-lat.pdf"

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 3.8in, (3.8*0.35)in
set output OUT_FN

x_min=-0.6
x_max=14.5 + 0.6
LW=2
PS=0.5
LMARGIN=0.17
RMARGIN=0.85
TMARGIN=0.96

# Legend
if (1) {
  set notics
  set noborder

  # Align the stacked plots
  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN
  set bmargin screen 0

  set xrange [x_min:x_max]

  #LC="#808080"
  LC="black"

  if (1) {
    x0=0-0.5
    x1=4+0.5
    y_c=0
    y_t=y_c+0.5
    y_b=y_c-0.5
    set arrow from x0,y_c to x1,y_c nohead lw LW lc rgb LC front
    set arrow from x0,y_t to x0,y_b nohead lw LW lc rgb LC front
    set arrow from x1,y_t to x1,y_b nohead lw LW lc rgb LC front

    x_c=(x0+x1)/2
    set label "Slow DB\nwith EBS Mag" at x_c,y_t center offset 0,1.5 front
  }

  if (1) {
    x0=5.5-0.5
    x1=14.5+0.5
    y_c=0
    y_t=y_c+0.5
    y_b=y_c-0.5
    set arrow from x0,y_c to x1,y_c nohead lw LW lc rgb LC front
    set arrow from x0,y_t to x0,y_b nohead lw LW lc rgb LC front
    set arrow from x1,y_t to x1,y_b nohead lw LW lc rgb LC front

    x_c=(x0+x1)/2
    set label "Fast DB\nwith Local SSD" at x_c,y_t center offset 0,1.5 front
  }

  f(x)=x
  plot f(x) w l lc rgb "white" not
}


# Throughput vs latency by storage devices
if (1) {
  reset
  set ylabel "Latency (ms)" offset 1,0
  set xtics nomirror tc rgb "white" ( \
      "1"   0 \
    , "1.5" 1 \
    , "2"   2 \
    , "2.5" 3 \
    , "3"   4 \
    ,  "1"  5.5 \
    ,  "5"  6.5 \
    , "10"  7.5 \
    , "20"  8.5 \
    , "30"  9.5 \
    , "40" 10.5 \
    , "50" 11.5 \
    , "60" 12.5 \
    , "70" 13.5 \
    , "80" 14.5 \
  )
  set ytics nomirror tc rgb "black"
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]

  logscale_y=1
  if (logscale_y == 1) {
    set logscale y
    set yrange [0.04:500]
  } else {
    set yrange [0:3]
  }

  F_TP=0
  b=6
  BW=0.25
  x_offset=0.18
  stg_dev="ebs-st1"

  # Legend
  if (1) {
    # Component organization off/on
    x0 = 0.376
    x01 = x0 + 0.01
    y0 = 0.90
    y01 = y0 - 0.455
    set arrow from graph x0,y0 to graph x0,y01 nohead lw 2 front
    set arrow from graph x0,y0 to graph x01,y0 nohead lw 2 front

    x1 = x0 + 0.023
    y1 = y0 - 0.155
    y11 = y1 - 0.08
    y12 = y11 - 0.22
    set arrow from graph x1,y11 to graph x1,y12 nohead lw 2 front

    x02 = x01 + 0.01
    #l0 = "Comp. org. off"
    #l1 = "Comp. org. on"
    l0 = "Unmodified DB"
    #l1 = "SSTable component organization"
    l1 = "Comp. org."
    set label l0 at graph x02,y0 left tc rgb "black" front
    set label l1 at graph x02,y1 left tc rgb "black" front

    # Percentiles and average
    x0 = 0.99
    x1 = x0 + 0.03
    y0 = 0.71
    set arrow from graph x0,y0 to graph x1,y0 nohead lw 2
    x2 = x1 + 0.01
    y01 = y0 + 0.04
    set label "99.99th" at graph x2,y01 left tc rgb "black" front

    y0 = y0 - 0.08
    y01 = y0 - 0.02
    set arrow from graph x0,y0 to graph x1,y0 nohead lw 2
    set label "99.9th"  at graph x2,y01 left tc rgb "black" front

    y0 = y0 - 0.11
    y01 = y0 - 0.04
    set arrow from graph x0,y0 to graph x1,y0 nohead lw 2
    set label "99th"  at graph x2,y01 left tc rgb "black" front

    y0 = y0 - 0.205
    y01 = y0
    set arrow from graph x0,y0 to graph x1,y0 nohead lw 2
    set label "90th"  at graph x2,y01 left tc rgb "black" front

    y0 = y0 - 0.10
    y01 = y0 - 0.03
    set arrow from graph x0,y0 to graph x1,y0 nohead lw 2
    set label "Avg"  at graph x2,y01 left tc rgb "black" front
  }

  x(a)=(a < 5 ? a : (a+0.5))

  set boxwidth BW

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  CS = 0.11

  plot IN_WO u (x($0) - x_offset):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) \
      w candlesticks lc rgb "blue" lw LW fs transparent solid 0.5 not whiskerbars, \
    IN_WO u (x($0) - x_offset):(column(b+0)/1000):(CS) w circles fs transparent solid 0.5 fc rgb "blue" not, \
    IN_W u (x($0) + x_offset):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) \
      w candlesticks lc rgb "red" lw LW fs transparent solid 0.15 not whiskerbars, \
    IN_W u (x($0) + x_offset):(column(b+0)/1000):(CS) w circles fs transparent solid 0.15 fc rgb "red" not

  # whisker plot: x box_min whisker_min whisker_high box_high
  #            iops      99          90        99.99     99.9
  #               3     7+1         7+0          7+3      7+2
}


# Latency increase or reduction
if (1) {
  reset
  set xlabel "K IOPS\n\n "
  #set ylabel "Relative change (%)" offset 1,0
  #set ylabel "Latency increase\nor reduction (%)" offset 0,0
  #set ylabel "Changes in\navg latency (%)" offset 0,0
  set ylabel "Change (%)" offset 0,0
  set xtics nomirror tc rgb "black" ( \
      "1"   0 \
    , "1.5" 1 \
    , "2"   2 \
    , "2.5" 3 \
    , "3"   4 \
    ,  "1"  5.5 \
    ,  "5"  6.5 \
    , "10"  7.5 \
    , "20"  8.5 \
    , "30"  9.5 \
    , "40" 10.5 \
    , "50" 11.5 \
    , "60" 12.5 \
    , "70" 13.5 \
    , "80" 14.5 \
  )
  set ytics nomirror tc rgb "black" autofreq -100,25
  set mytics 2
  set grid xtics ytics back lc rgb "black"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]
  set yrange [-70:20]

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  # Legend
  if (1) {
    xc = 2
    yc = -55
    x_w = 1.4
    y_w = 8
    x0 = xc - x_w
    x1 = xc + x_w
    y0 = yc - y_w
    y1 = yc + y_w
    #set obj rect from x0,y0 to x1,y1 fs noborder transparent solid 0.8 front
    set label "-36.85%" at xc, yc center tc rgb "red" front

    xc = 10
    yc = -30
    set label "-1.47%" at xc, yc center tc rgb "red" front
  }

  x_w2=0.22

  plot IN_W_O_WO_LAT u (x($0)-x_w2):($3*100 - 100):(x($0)-x_w2):(x($0)+x_w2):(0):($3*100 - 100) w boxxyerrorbars \
    fs transparent solid 0.3 fc rgb "black" not

  # Blue for decreases, red for increases
  if (0) {
    TP=0.3
    plot IN_W_O_WO_LAT u (x($0)-x_w2):($3 < 1.0 ? $3*100 - 100 : 1/0):(x($0)-x_w2):(x($0)+x_w2):(0):($3*100 - 100) w boxxyerrorbars \
      lc rgb "blue" fillstyle transparent solid TP not, \
    IN_W_O_WO_LAT u (x($0)-x_w2):(1.0 <= $3 ? $3*100 - 100 : 1/0):(x($0)-x_w2):(x($0)+x_w2):(0):($3*100 - 100) w boxxyerrorbars \
      lc rgb "red" fillstyle transparent solid TP not
  }

  # boxxyerrorbars
  # x  y  xlow  xhigh  ylow  yhigh
}


TP_MD_OFF = 0.5
TP_MD_ON = 0.15

x_w=0.26
x_spacing=0.05

# File system cache size
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "File system\ncache size (GB)" offset 1,0
  set xtics nomirror tc rgb "black" ( \
      "1"   0 \
    , "1.5" 1 \
    , "2"   2 \
    , "2.5" 3 \
    , "3"   4 \
    ,  "1"  5.5 \
    ,  "5"  6.5 \
    , "10"  7.5 \
    , "20"  8.5 \
    , "30"  9.5 \
    , "40" 10.5 \
    , "50" 11.5 \
    , "60" 12.5 \
    , "70" 13.5 \
    , "80" 14.5 \
  )
  set ytics nomirror tc rgb "black" autofreq 0,0.1
  set mytics 2
  set grid ytics mytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]
  set yrange [4.25:4.55]

  # Legend
  if (1) {
    x0 = 0.376
    x01 = x0 + 0.01
    y0 = 0.91
    y01 = y0 - 0.235
    set arrow from graph x0,y0 to graph x0,y01 nohead lw 2 front
    set arrow from graph x0,y0 to graph x01,y0 nohead lw 2 front

    x1 = x0 + 0.023
    y1 = y0 - 0.155
    y11 = y1 - 0.08
    y12 = y11 - 0.16
    set arrow from graph x1,y11 to graph x1,y12 nohead lw 2 front

    x02 = x01 + 0.01
    set label "Comp. org. off" at graph x02,y0 left tc rgb "black" front
    set label "Comp. org. on (xx% lower)"  at graph x02,y1 left tc rgb "black" front
  }

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  x1=0-x_spacing
  x2=x_spacing
  x0=x1-x_w
  x3=x2+x_w

  plot \
  IN_W_O_WO_MEM u (x($0)+x0):($5/1024):(x($0)+x0):(x($0)+x1):(0):($5/1024) w boxxyerrorbars \
    lc rgb "blue" lw LW fs border transparent solid TP_MD_OFF not, \
  IN_W_O_WO_MEM u (x($0)+x2):($3/1024):(x($0)+x2):(x($0)+x3):(0):($3/1024) w boxxyerrorbars \
    lc rgb "red" lw LW fs border transparent solid TP_MD_ON not
}


# DB process memory usage
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "DB process\nmemory size (GB)" offset 0.5,0
  set xtics nomirror tc rgb "black" ( \
      "1"   0 \
    , "1.5" 1 \
    , "2"   2 \
    , "2.5" 3 \
    , "3"   4 \
    ,  "1"  5.5 \
    ,  "5"  6.5 \
    , "10"  7.5 \
    , "20"  8.5 \
    , "30"  9.5 \
    , "40" 10.5 \
    , "50" 11.5 \
    , "60" 12.5 \
    , "70" 13.5 \
    , "80" 14.5 \
  )
  set ytics nomirror tc rgb "black" autofreq 0,0.05 format "%.2f"
  set mytics 2
  set grid ytics mytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]
  set yrange [0.85:1.1]

  # Legend
  if (1) {
    x0 = 0.376
    x01 = x0 + 0.01
    y0 = 0.91
    y01 = y0 - 0.52
    set arrow from graph x0,y0 to graph x0,y01 nohead lw 2 front
    set arrow from graph x0,y0 to graph x01,y0 nohead lw 2 front

    x1 = x0 + 0.023
    y1 = y0 - 0.155
    y11 = y1 - 0.08
    y12 = y11 - 0.12
    set arrow from graph x1,y11 to graph x1,y12 nohead lw 2 front

    x02 = x01 + 0.01
    set label "Comp. org. off" at graph x02,y0 left tc rgb "black" front
    set label "Comp. org. on (xx% higher)"  at graph x02,y1 left tc rgb "black" front
  }

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN
  set tmargin screen TMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  x1=0-x_spacing
  x2=x_spacing
  x0=x1-x_w
  x3=x2+x_w

  plot \
  IN_W_O_WO_MEM u (x($0)+x0):($6/1024):(x($0)+x0):(x($0)+x1):(0):($6/1024) w boxxyerrorbars \
    lc rgb "blue" lw LW fs border transparent solid TP_MD_OFF not, \
  IN_W_O_WO_MEM u (x($0)+x2):($4/1024):(x($0)+x2):(x($0)+x3):(0):($4/1024) w boxxyerrorbars \
    lc rgb "red" lw LW fs border transparent solid TP_MD_ON not
}

print sprintf("Created %s", OUT_FN)
