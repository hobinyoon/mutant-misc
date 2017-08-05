# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("FN_IN=%s", FN_IN)
#print sprintf("FN_OUT=%s", FN_OUT)

set xdata time
# 0711-170251
set timefmt "%m%d-%H%M%S"
set format x "%d"

# Get data range
if (1) {
	set terminal unknown
	plot FN_IN u 25:29 w l
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
}

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080" back
set grid xtics ytics mytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0,24*3600
set ytics nomirror tc rgb "black" #autofreq 0,2*60*60
set mytics 2
set tics front

set xlabel "Time (day)"
set ylabel "CPU usage (%)"

set xrange[X_MIN:X_MAX]
set yrange[0:100]

set samples 1000

plot \
FN_IN u 25:($29+$30) w p pt 7 pointsize 0.15 lc rgb "#8080FF" not, \
FN_IN u 25:29        w p pt 7 pointsize 0.15 lc rgb "#FF8080" not, \
FN_IN u 25:30        w p pt 7 pointsize 0.15 lc rgb "#80FF80" not, \
FN_IN u 25:($29+$30) w l smooth bezier lw 4 lc rgb "#0000FF" t "total", \
FN_IN u 25:30        w l smooth bezier lw 4 lc rgb "#FF0000" t "sys"  , \
FN_IN u 25:29        w l smooth bezier lw 4 lc rgb "#00FF00" t "user" , \

# iowait is a sub-category of idle. When the system load is low, you see get a
# high cpu wait time. When high, iowait time is hidden by CPU interleaving, I
# think. So, it's not a good indicator of telling whether the system is
# overloaded or not.
# http://serverfault.com/questions/12679/can-anyone-explain-precisely-what-iowait-is
#FN_IN u 25:31 w l t "io wait", \

#FN_IN u 25:27 w l t "idle", \
