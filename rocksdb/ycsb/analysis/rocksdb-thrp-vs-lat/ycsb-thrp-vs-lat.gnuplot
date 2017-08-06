# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEY)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

if (1) {
  set noxtics
  set noytics
  set noborder
  f(x) = x
  set label 1 at screen 0.5, screen 0.5 \
    "1: read latency\n1: read latency" \
    center
  plot f(x) lc rgb "#F0F0F0" not
}

unset label 1

set xtics nomirror tc rgb "black" ( \
   "0"      0 \
,  "2"  20000 \
,  "4"  40000 \
,  "6"  60000 \
,  "8"  80000 \
, "10" 100000 \
, "12" 120000 \
, "14" 140000 \
)

set ytics nomirror tc rgb "black" ( \
  "1"          1 \
, "10"        10 \
, "10^2"     100 \
, "10^3"    1000 \
, "10^4"   10000 \
, "10^5"  100000 \
, "10^6" 1000000 \
)

#set ytics nomirror tc rgb "black" ( \
#   "0"      0 \
#,  "2"  2000 \
#,  "4"  4000 \
#,  "6"  6000 \
#,  "8"  8000 \
#, "10" 10000 \
#, "12" 12000 \
#, "14" 14000 \
#)

set grid xtics mxtics ytics back lc rgb "#808080"
set border (1+2+4+8) back lc rgb "#808080"


set xlabel "IOPS (10K IOs/sec)"
set ylabel "Latency (ms)" offset -0.5, 0

set xrange [0:140000]
#set yrange [0:]

set logscale y

plot \
FN_IN u 2:6:6:6:6 w candlesticks lw 2 lc rgb "red" not, \
FN_IN u 2:5:4:9:7 w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
FN_IN u 2:3 w p pt 7 ps 0.4 lc rgb "red" not

#     ''                 using 1:4:4:4:4 with candlesticks lt -1 lw 2 notitle

# candlesticks
# x  box_min  whisker_min  whisker_high  box_high

#plot \
#FN_IN u 2:3 w lp pt 7 ps 0.3 lc rgb "red" not, \

#FN_IN u 2:4 w lp pt 7 ps 0.3 lc rgb "blue" not, \
#FN_IN u 2:5 w lp pt 7 ps 0.3 lc rgb "green" not, \

if (0) {
set mxtics 2
set ytics nomirror tc rgb "black"
#(\
#  "10^1"     10 \
#, "10^2"    100 \
#, "10^3"   1000 \
#, "10^4"  10000 \
#, "10^5" 100000 \
#)
#set mytics
set tics front

# http://www.gnuplot.info/docs_4.2/gnuplot.html#x1-18600043.21.2
#set format y '10^{%T}'

set xlabel "Time (hour)" offset 0,0.3
set ylabel "IOPS (K ops/sec)" offset 1.5,0

#set size 1, 0.97
#set key center at graph 0.5, 1.09 maxrows 1 samplen 0.5

set xrange[0:]
#set yrange[30:20000]

#set logscale y

plot \
FN_IN u ($1/3600):($6 == -1 ? 1/0 : ($6 == 0 ? 1/0 : $6/1000)) w p pt 1 pointsize 0.3 lc rgb "red" not

#plot \
#FN_IN u (-1):(1) w p pt 2 pointsize 0.6 lc rgb "red"  lw 4 t "Insert", \
#FN_IN u (-1):(1) w p pt 1 pointsize 0.6 lc rgb "blue" lw 4 t "Read", \
#FN_IN u ($1/3600):($2 == -1 ? 1/0 : $2) w p pt 1 pointsize 0.3 lc rgb "blue" not , \
#FN_IN u ($1/3600):($4 == -1 ? 1/0 : $4) w p pt 2 pointsize 0.3 lc rgb "red"  not

}
