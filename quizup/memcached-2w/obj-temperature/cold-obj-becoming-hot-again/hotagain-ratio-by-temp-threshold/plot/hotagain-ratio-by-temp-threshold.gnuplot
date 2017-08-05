#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN = "data"
FN_OUT = "hotagain-ratio-by-temp-threshold.pdf"

set print "-"

set terminal unknown
plot \
FN_IN u 1:($4/100) w lp
Y_MIN=GPVAL_DATA_Y_MIN

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set xlabel "Cold-to-hot temperature threshold"
set ylabel "Cold-to-hot object ratio"

set border front lc rgb "#808080" back
set grid back xtics ytics
set xtics nomirror tc rgb "black" ( \
"2^0" 1 \
, "" 2 \
, "2^2" 4 \
, "" 8 \
, "2^4" 16 \
, "" 32 \
, "2^6" 64 \
, "" 128 \
, "2^8" 256 \
, "" 512 \
, "2^{10}" 1024 \
, ""       2048 \
, "2^{12}" 4096 \
)
set ytics nomirror tc rgb "black"
set nomytics
set tics back

set format x '10^{%T}'
set format y '10^{%T}'

set logscale xy

set yrange [Y_MIN:]

#x0=20
#y0=2.016600/100.0
#set arrow from x0,Y_MIN to x0,y0 lc rgb "blue" lw 6 lt 0 nohead

plot \
FN_IN u 1:($4/100.0) w lp lw 2 pt 7 pointsize 0.3 not, \
FN_IN u ($1==20 ? $1:1/0):($4/100.0) w p lw 2 pt 7 pointsize 0.5 lc rgb "blue" not, \
FN_IN u ($1==20 ? $1:1/0):($4/100.0):(sprintf("(%d, %.4f)", $1, $4/100.0)) w labels left offset 0.7,0.7 tc rgb "blue" not

print sprintf("Created %s", FN_OUT)
