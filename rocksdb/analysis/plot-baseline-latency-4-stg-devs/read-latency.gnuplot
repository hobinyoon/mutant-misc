# Tested with gnuplot 4.6 patchlevel 4

FN_IN_LOCAL_SSD = system("echo $FN_IN_LOCAL_SSD")
FN_IN_EBS_GP2 = system("echo $FN_IN_EBS_GP2")
FN_IN_EBS_ST1 = system("echo $FN_IN_EBS_ST1")
FN_IN_EBS_SC1 = system("echo $FN_IN_EBS_SC1")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("FN_OUT=%s", FN_OUT)

set xdata time
# 160711-170810.831
set timefmt "%y%m%d-%H%M%S"
set format x "%d-%H"

# Get data range
# Even gp2, the most stable one, has a very high y max. Manually set.
if (0) {
	set terminal unknown
	plot FN_IN_EBS_GP2 u 4:($19/1000.0) w p
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
	Y_MAX=GPVAL_DATA_Y_MAX
}

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080" back
set grid xtics mxtics ytics mytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0,4*3600
set mxtics 4
set ytics nomirror tc rgb "black"
set mytics 2
set tics front

set xlabel "Time (day-hour)"
set ylabel "Latency (ms)"

#set xrange[X_MIN:X_MAX]
set xrange["160726-200000.000":"160727-110000.000"]

set samples 1000

PS=0.15
LW=4

COLORS="#0000FF #006400 #A52A2A #FF0000"
COLORS_LIGHT="#8080FF #80CB80 #E1B8B8 #FF8080"

set key horiz maxrows 1 width 0

metric_name="avg 99th 99.1th 99.2th 99.3th 99.4th 99.5th 99.6th 99.7th 99.8th 99.9th 99.91th 99.92th 99.93th 99.94th 99.95th 99.96th 99.97th 99.98th 99.99th"
y_min=      "  0   20     20     20     20     20     20     20     20     20     20      20      20      20      20      20      20      20      20      20"
y_max=      " 50   80     80     80     80     80     80   5000   5000   5000   5000   20000   20000   20000   20000   20000   20000   20000   30000   50000"
# metric_idx: 30 to 49

do for [i=1:20] {
	metric_idx=i+29
	set yrange[word(y_min,i)+0:word(y_max,i)+0]
	if (i == 1) {
		set title "Read latency: avg"
	} else {
		set title "Read latency: " . word(metric_name, i) . " percentile"
	}

	plot \
	FN_IN_EBS_SC1   u 4:(column(metric_idx)/1000.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 4:(column(metric_idx)/1000.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 4:(column(metric_idx)/1000.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 4:(column(metric_idx)/1000.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 4:(column(metric_idx)/1000.0) w l smooth bezier lw LW  lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 4:(column(metric_idx)/1000.0) w l smooth bezier lw LW  lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 4:(column(metric_idx)/1000.0) w l smooth bezier lw LW  lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 4:(column(metric_idx)/1000.0) w l smooth bezier lw LW  lc rgb word(COLORS, 1) t "EBS MagCold"
}
