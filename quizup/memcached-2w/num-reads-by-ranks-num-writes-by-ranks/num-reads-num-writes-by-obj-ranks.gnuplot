#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN_R=".output/num-reads-by-obj-ranks"
FN_IN_W=".output/num-writes-by-obj-ranks"
FN_OUT=".output/quizup-num-reads-num-writes-by-obj-ranks.pdf"

if (1) {
	set terminal unknown
	plot FN_IN_R u 1:2 w p
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
	Y_MIN=GPVAL_DATA_Y_MIN
	Y_MAX=GPVAL_DATA_Y_MAX
}

set print "-"
print sprintf("%f", Y_MAX)

set logscale xy

set terminal pdfcairo enhanced size 2.5in, (2.5*0.85)in
set output FN_OUT

set border back lc rgb "#808080"

set grid xtics ytics back lc rgb "black"
set xtics nomirror tc rgb "black"
set ytics nomirror tc rgb "black"
set nomxtics
set nomytics

set format x "10^%T"
set format y "10^%T"

set xlabel "Record rank" offset 0,-0.1
set ylabel "Number of accesses" offset -1,0
set xrange[1:X_MAX+1]

LW=4

plot \
FN_IN_R u ($1+1):2 w l lw LW lc rgb "red" t "Reads", \
FN_IN_W u ($1+1):2 w l lw LW lc rgb "blue" t "Writes", \

# Normalized y-axis
set ylabel "Access frequency (normalized)" offset -1,0
set ytics nomirror tc rgb "black" ( \
	"1" 1, \
	"10^{-1}" 0.1, \
	"10^{-2}" 0.01, \
	"10^{-3}" 0.001, \
	"10^{-4}" 0.0001, \
	"10^{-5}" 0.00001, \
	"10^{-6}" 0.000001 \
)
set yrange[:1]
plot \
FN_IN_R u ($1+1):($2/Y_MAX) w l lw LW lc rgb "red" t "Reads", \
FN_IN_W u ($1+1):($2/Y_MAX) w l lw LW lc rgb "blue" t "Writes", \

print sprintf("Created %s", FN_OUT)
