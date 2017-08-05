#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN = "data"
FN_OUT = "per-obj-initial-hot-region-max-temperature-CDF.pdf"

set print "-"

set terminal unknown
plot \
FN_IN u 1:2 w l
X_MAX=GPVAL_DATA_X_MAX

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set xlabel "Initial hot region\nmax temperature"
set ylabel "CDF" offset 0.8,0

set border front lc rgb "#808080" back
set grid back xtics ytics
set xtics nomirror tc rgb "black"
set ytics nomirror format "%.1f" tc rgb "black"
set nomytics
set tics back

set format x '10^{%T}'

set logscale x

set xrange [:X_MAX]

plot \
FN_IN u 1:2 w l lw 3 not

print sprintf("Created %s", FN_OUT)
