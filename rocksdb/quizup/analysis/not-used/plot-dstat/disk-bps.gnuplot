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
set ylabel "Disk IO (MB/s)"

set xrange[X_MIN:X_MAX]

set samples 1000

data_disk = "EBS st1"

if (data_disk eq "Local SSD") {
	set yrange[0:]
	plot \
	FN_IN u 25:($6/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#FF8080" not, \
	FN_IN u 25:($5/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#8080FF" not, \
	FN_IN u 25:($6/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "red"  t "Local SSD (RocksDB data) - write", \
	FN_IN u 25:($5/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "blue" t "Local SSD (RocksDB data) - read"
} else {
if ((data_disk eq "EBS gp2") || (data_disk eq "EBS st1") || (data_disk eq "EBS sc1")) {
	set yrange[0:40]
	plot \
	FN_IN u 25:($8/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#FF8080" not, \
	FN_IN u 25:($7/1024.0/1024.0) w p pt 7 pointsize 0.15 lc rgb "#8080FF" not, \
	FN_IN u 25:($8/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "red"  t data_disk . " (RocksDB data) - write", \
	FN_IN u 25:($7/1024.0/1024.0) w l smooth bezier lw 4 lc rgb "blue" t data_disk . " (RocksDB data) - read"
} }

#FN_IN u 25:($3/1024.0/1024.0) w p t "Local SSD (program binaries, workload data) - read", \
#FN_IN u 25:($4/1024.0/1024.0) w p t "Local SSD (program binaries, workload data) - write", \

# EBS SSD was not used
#FN_IN u 25:($8/1024.0/1024.0) w l t "EBS SSD (Not used) - write", \
#FN_IN u 25:($7/1024.0/1024.0) w l t "EBS SSD (Not used) - read", \

# System disk. Didn't want a distraction. Too little.
#FN_IN u 25:($1/1024.0/1024.0) w l t "xvda - read", \
#FN_IN u 25:($2/1024.0/1024.0) w l t "xvda - write", \

# boxxyerrorbars: x y xlow xhigh ylow yhigh
