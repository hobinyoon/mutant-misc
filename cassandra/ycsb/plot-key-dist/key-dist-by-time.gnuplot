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
FN_IN u 0:1 w p pt 7 pointsize 0.3 not
Y_MAX=GPVAL_DATA_Y_MAX

print sprintf("Y_MAX=%.0f", Y_MAX)
#----------------------------------------------------------

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set xtics rotate by -45

set yrange [0:Y_MAX]

plot \
FN_IN u 0:1 w p pt 7 pointsize 0.05 not
