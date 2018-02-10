# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
NUM_OBJS = system("echo $NUM_OBJS") + 0
PER_OBJ = system("echo $PER_OBJ") + 0
FN_OUT = system("echo $FN_OUT")

plot_logscalex=0

set print "-"

# Get data range
set terminal unknown
if (PER_OBJ) {
	plot FN_IN u ($1+1):($2/NUM_OBJS) w l
} else {
	plot FN_IN u ($1+1):($2) w l
}
Y_MIN=GPVAL_DATA_Y_MIN
Y_MAX=GPVAL_DATA_Y_MAX

set border back lc rgb "#808080"

#set grid xtics mxtics back lc rgb "black"
set grid xtics ytics back lc rgb "#C0C0C0" #lw 2

if (PER_OBJ) {
	set ylabel "Reads / min / object" offset 0,0
} else {
	#set ylabel "Reads / min" offset 0,0
	set ylabel "Read freq (relative)" offset 0,0
}

set tmargin screen 0.97
set rmargin screen 0.95

if (plot_logscalex) {
	set xtics nomirror tc rgb "black" ( \
	"1m" 1 \
	, "1h" 60 \
	, "1d" 24 * 60 \
	, "1w" 7 * 24 * 60 \
	, ""   2 * 7 * 24 * 60 \
	)
	set xlabel "Object age" offset 0,0.1
} else {
	set xtics nomirror tc rgb "black" ( \
	"0"   0 * 24 * 60 \
	, ""  1 * 24 * 60 \
	, "2" 2 * 24 * 60 \
	, ""  3 * 24 * 60 \
	, "4" 4 * 24 * 60 \
	, ""  5 * 24 * 60 \
	, "6" 6 * 24 * 60 \
	, ""  7 * 24 * 60 \
	, "8" 8 * 24 * 60 \
	, ""  9 * 24 * 60 \
	, "10" 10 * 24 * 60 \
	, ""   11 * 24 * 60 \
	, "12" 12 * 24 * 60 \
	, ""   13 * 24 * 60 \
	, "14" 14 * 24 * 60 \
	, ""   15 * 24 * 60 \
	, "16" 16 * 24 * 60 \
	)
	set xlabel "Object age (day)" offset 0,0.1
}

if (PER_OBJ) {
	set ytics nomirror left offset -3.2,0 tc rgb "black"
	set format y "10^{%T}"
} else {
	set ytics nomirror right offset 0,0 tc rgb "black" ( \
	"1" Y_MAX \
	, "10^{-1}" Y_MAX/10 \
	, "10^{-2}" Y_MAX/100 \
	, "10^{-3}" Y_MAX/1000 \
	, "10^{-4}" Y_MAX/10000 \
	, "10^{-5}" Y_MAX/100000 \
	, "10^{-6}" Y_MAX/1000000 \
	, "10^{-7}" Y_MAX/10000000 \
	)
	#set ytics nomirror left offset -3.2,0 tc rgb "black" ( \
	#"10^0" Y_MAX \
	#, "10^{-1}" Y_MAX/10 \
	#, "10^{-2}" Y_MAX/100 \
	#, "10^{-3}" Y_MAX/1000 \
	#, "10^{-4}" Y_MAX/10000 \
	#, "10^{-5}" Y_MAX/100000 \
	#, "10^{-6}" Y_MAX/1000000 \
	#, "10^{-7}" Y_MAX/10000000 \
	#)
}
set nomytics
set tics front

set terminal pdfcairo enhanced size 2.2in, (2.2*0.90)in
set output FN_OUT

set xrange[1:16*24*60]
set yrange[Y_MIN:]

if (plot_logscalex) {
	set logscale xy
} else {
	set logscale y
}

# Plot twice to make the key line thicker
LW_1min=1
LW_1hr=4
LW_key=8
if (PER_OBJ) {
	plot FN_IN u ($1+1):($2/NUM_OBJS) w l lw LW_1min lc rgb "#808080" not, \
	FN_IN u ($1+1):($3/NUM_OBJS) w l lw LW_1hr lc rgb "red" not, \
	FN_IN u ($1+1):(Y_MIN/2) w l lw LW_key lc rgb "#808080" t "1-min avg", \
	FN_IN u ($1+1):(Y_MIN/2) w l lw LW_key lc rgb "red" t "1-hour avg", \
} else {
	plot FN_IN u ($1+1):($2) w l lw LW_1min lc rgb "#808080" not, \
	FN_IN u ($1+1):($3) w l lw LW_1hr lc rgb "red" not, \
	FN_IN u ($1+1):(Y_MIN/2) w l lw LW_key lc rgb "#808080" t "1-min avg", \
	FN_IN u ($1+1):(Y_MIN/2) w l lw LW_key lc rgb "red" t "1-hour avg", \
}
