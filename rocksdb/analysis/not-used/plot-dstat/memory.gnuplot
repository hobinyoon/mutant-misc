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
set ytics nomirror tc rgb "black"
set mytics 2
set tics front

set xlabel "Time (day)"
set ylabel "Memory usage (GB)"

set xrange[X_MIN:X_MAX]
set yrange[0:]

plot \
FN_IN u 25:($19/1024.0/1024.0) w l t "free", \
FN_IN u 25:($20/1024.0/1024.0) w l t "used", \
FN_IN u 25:($18/1024.0/1024.0) w l t "cache", \
FN_IN u 25:($17/1024.0/1024.0) w l t "buffer", \

# http://stackoverflow.com/questions/6345020/linux-memory-buffer-vs-cache
#
# Buffers are associated with a specific block device, and cover caching of
# filesystem metadata as well as tracking in-flight pages. The cache only
# contains parked file data. That is, the buffers remember what's in
# directories, what file permissions are, and keep track of what memory is
# being written from or read to for a particular block device. The cache only
# contains the contents of the files themselves.
