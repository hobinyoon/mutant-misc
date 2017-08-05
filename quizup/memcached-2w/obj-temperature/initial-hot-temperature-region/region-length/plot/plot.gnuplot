#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN_UNTIL_COLD = "data-initial-hot-region-length-until-cold"
FN_IN_UNTIL_LAST_REQ = "data-initial-hot-region-length-until-last_req"
FN_OUT = "per-obj-initial-hot-region-length-CDF.pdf"

set print "-"

set terminal unknown
plot \
FN_IN_UNTIL_COLD u 1:2 w l
X_MAX=GPVAL_DATA_X_MAX

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set xlabel "Initial hot region\nlength (min)"
set ylabel "CDF" offset 0.8,0

set border front lc rgb "#808080" back
set grid back xtics ytics
set xtics nomirror tc rgb "black"
set ytics nomirror format "%.1f" tc rgb "black"
set nomytics
set tics back

set format x '10^{%T}'

x_logscale=1

if (x_logscale) {
	set logscale x
	set xrange [:X_MAX]
} else {
	set xrange [:300]
}

set key at screen 0.1,0.9 left

plot \
FN_IN_UNTIL_LAST_REQ u 1:2 w l lw 3 t "Until last req", \
FN_IN_UNTIL_COLD u 1:2 w l lw 3 t "Until cold"

print sprintf("Created %s", FN_OUT)
