#! /usr/bin/gnuplot

# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEY)

#----------------------------------------------------------
# Get data range
set terminal unknown
plot \
FN_IN u ($0+1):2 w p pt 7 pointsize 0.05 not
X_MIN=GPVAL_DATA_X_MIN
X_MAX=GPVAL_DATA_X_MAX
Y_MIN=GPVAL_DATA_Y_MIN
Y_MAX=GPVAL_DATA_Y_MAX

print sprintf("X_MIN=%.0f X_MAX=%.0f Y_MIN=%.0f Y_MAX=%.0f", X_MIN, X_MAX, Y_MIN, Y_MAX)
#----------------------------------------------------------

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border back
set grid xtics mxtics ytics mytics
#set xtics rotate by -45

set xlabel "Rank (starts from 1)"
set xlabel "Number of occurrences"

set xrange [X_MIN:X_MAX]
set yrange [Y_MIN:Y_MAX]

set logscale xy

plot \
FN_IN u ($0+1):2 w lp pt 7 pointsize 0.2 lw 2 not
