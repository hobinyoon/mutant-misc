# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("FN_IN=%s", FN_IN)
#print sprintf("FN_OUT=%s", FN_OUT)

set xdata time
# 160711-170810.831
set timefmt "%y%m%d-%H%M%S"
set format x "%d"

# Get data range
if (1) {
	set terminal unknown
	plot FN_IN u 4:($16/1000.0) w l
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
set ylabel "Latency (ms)"

set xrange[X_MIN:X_MAX]
set yrange[0:1000]

set samples 1000

plot \
FN_IN u 4:($16/1000.0) w p pt 7 pointsize 0.15 lc rgb "#FF8080" not, \
FN_IN u 4:($15/1000.0) w p pt 7 pointsize 0.15 lc rgb "#80FF80" not, \
FN_IN u 4:($14/1000.0) w p pt 7 pointsize 0.15 lc rgb "#8080FF" not, \
FN_IN u 4:($16/1000.0) w l smooth bezier lw 4 lc rgb "#FF0000" t "get 99.9th", \
FN_IN u 4:($15/1000.0) w l smooth bezier lw 4 lc rgb "#00FF00" t "get 99th"  , \
FN_IN u 4:($14/1000.0) w l smooth bezier lw 4 lc rgb "#0000FF" t "get avg"   , \

#FN_IN u 25:($6/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#FF8080" t "Local SSD (RocksDB data) - write", \
#FN_IN u 25:($5/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#8080FF" t "Local SSD (RocksDB data) - read", \
#FN_IN u 25:($6/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "red"  not, \
#FN_IN u 25:($5/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "blue" not, \

#FN_IN u 4:($17/1000.0) w l t "get 99.9.9", \
