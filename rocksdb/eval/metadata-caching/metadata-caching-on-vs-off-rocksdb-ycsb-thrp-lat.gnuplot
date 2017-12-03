#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 6

IN_W_O_WO_LAT = "data/with-over-wo"
IN_W = "data/with-metadata-caching"
IN_WO = "data/wo-metadata-caching"
IN_W_O_WO_MEM = "data/memory-usage"
OUT_FN = "metadata-caching-on-vs-off-rocksdb-ycsbd-thrp-vs-lat.pdf"

set print "-"
#print sprintf("TIME_MAX=%s", TIME_MAX)

set terminal pdfcairo enhanced size 4.3in, (4.3*0.35)in
set output OUT_FN

x_min=-0.5
x_max=15
LW=2
PS=0.5
LMARGIN=9

# Legend
if (1) {
  set notics
  set noborder

  # Align the stacked plots
  set lmargin LMARGIN
  set bmargin 0

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
    set label "EBS Mag" at x_c,y_t center offset 0,0.5
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
    set label "Local SSD" at x_c,y_t center offset 0,0.5
  }

  f(x)=x
  plot f(x) w l lc rgb "white" not
}


# Throughput vs latency by storage devices
if (1) {
  reset
  set xlabel "K IOPS"
  set ylabel "Latency (ms)" offset 1,0
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
  set ytics nomirror tc rgb "black"
  set grid ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]

  logscale_y=1
  if (logscale_y == 1) {
    set logscale y
    set yrange [0.05:400]
  } else {
    set yrange [0:3]
  }

  F_TP=0
  b=6
  BW=0.25
  x_offset=0.18
  stg_dev="ebs-st1"

  set label "Metadata\ncaching\nOff" at 7.5-x_offset,150 center tc rgb "blue"
  set label "On"                     at 9.5+x_offset,25  center tc rgb "red"

  x(a)=(a < 5 ? a : (a+0.5))

  set boxwidth BW

  set lmargin LMARGIN

  plot IN_WO u (x($0) - x_offset):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) \
      w candlesticks lc rgb "blue" lw LW fillstyle transparent solid F_TP not whiskerbars, \
    IN_WO u (x($0) - x_offset):(column(b+0)/1000) w p pt 7 lc rgb "blue" ps PS not, \
    IN_W u (x($0) + x_offset):(column(b+2)/1000):(column(b+1)/1000):(column(b+4)/1000):(column(b+3)/1000) \
      w candlesticks lc rgb "red" lw LW fillstyle pattern 2 not whiskerbars, \
    IN_W u (x($0) + x_offset):(column(b+0)/1000) w p pt 7 lc rgb "red" ps PS not

  # whisker plot: x box_min whisker_min whisker_high box_high
  #            iops      99          90        99.99     99.9
  #               3     7+1         7+0          7+3      7+2
}


TP=0.3

# Latency increase or reduction
if (1) {
  reset
  set xlabel "K IOPS"
  #set ylabel "Relative change (%)" offset 1,0
  set ylabel "Latency increase\nor reduction (%)" offset 0.5,0
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
  set ytics nomirror tc rgb "black" autofreq -100,20
  set mytics 2
  set grid ytics mytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange [x_min:x_max]
  set yrange [-70:20]

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin LMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  x_w2=0.22

  plot IN_W_O_WO_LAT u (x($0)-x_w2):($3 < 1.0 ? $3*100 - 100 : 1/0):(x($0)-x_w2):(x($0)+x_w2):(0):($3*100 - 100) w boxxyerrorbars \
    lc rgb "blue" fillstyle transparent solid TP not, \
  IN_W_O_WO_LAT u (x($0)-x_w2):(1.0 <= $3 ? $3*100 - 100 : 1/0):(x($0)-x_w2):(x($0)+x_w2):(0):($3*100 - 100) w boxxyerrorbars \
    lc rgb "red" fillstyle transparent solid TP not

  # boxxyerrorbars
  # x  y  xlow  xhigh  ylow  yhigh
}


x_w=0.25
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
  set yrange [4.3:4.5]

  set label "Metadata\ncaching\nOff" at 9.5-x_offset    ,4.5 center tc rgb "blue" front
  set label "On"                     at 9.5+x_offset+0.2,4.4 center tc rgb "red"  front

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin LMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  x1=0-x_spacing
  x2=x_spacing
  x0=x1-x_w
  x3=x2+x_w

  plot \
  IN_W_O_WO_MEM u (x($0)+x0):($5/1024):(x($0)+x0):(x($0)+x1):(0):($5/1024) w boxxyerrorbars \
    lc rgb "blue" lw LW fillstyle pattern 0 not, \
  IN_W_O_WO_MEM u (x($0)+x2):($3/1024):(x($0)+x2):(x($0)+x3):(0):($3/1024) w boxxyerrorbars \
    lc rgb "red" lw LW fillstyle pattern 2 not
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
  set yrange [0.9:1.05]

  set label "Metadata\ncaching\nOff" at 9.5-x_offset    ,1.045 center tc rgb "blue" front
  set label "On"                     at 9.5+x_offset+0.2,0.965 center tc rgb "red"  front

  x(a)=(a < 5 ? a : (a+0.5))

  set lmargin LMARGIN

  set arrow from x_min,0 to x_max,0 lc rgb "#808080" nohead

  x1=0-x_spacing
  x2=x_spacing
  x0=x1-x_w
  x3=x2+x_w

  plot \
  IN_W_O_WO_MEM u (x($0)+x0):($4/1024):(x($0)+x0):(x($0)+x1):(0):($4/1024) w boxxyerrorbars \
    lc rgb "blue" lw LW fillstyle pattern 0 not, \
  IN_W_O_WO_MEM u (x($0)+x2):($6/1024):(x($0)+x2):(x($0)+x3):(0):($6/1024) w boxxyerrorbars \
    lc rgb "red" lw LW fillstyle pattern 2 not
}
