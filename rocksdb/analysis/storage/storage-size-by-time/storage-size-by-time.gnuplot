# Tested with gnuplot 4.6 patchlevel 4

IN_FN_M = system("echo $IN_FN_M")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set xdata time
# 160711-170502.871
set timefmt "%y%m%d-%H%M%S"
set format x "%d"

# Get x range
if (1) {
	set terminal unknown
	plot IN_FN_M u 1:16:3:(0) w vectors
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
	Y_MAX=GPVAL_DATA_Y_MAX
	print sprintf("X_MIN=%d X_MAX=%d Y_MAX=%d", X_MIN, X_MAX, Y_MAX)
}

set terminal pdfcairo enhanced size 3in, (2.3*0.85)in
set output OUT_FN

set border front lc rgb "#808080" front
set grid xtics mxtics ytics front lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 24*3600, 2*24*3600
set mxtics 2
set ytics nomirror tc rgb "black" ( \
"4" 4000, \
"3" 3000, \
"2" 2000, \
"1" 1000, \
"0"    0 \
)
set tics front

set xlabel "Time (day)"
set ylabel "Total SSTable size (GB)" offset 0,0

# Trim the rightmost vertical line with X_MAX-1
set xrange[X_MIN:X_MAX-1]
set yrange[0:3300]

#set key top left reverse width -3

# Transparency of areas
TRANS=0.2

# Manual plotting of legend
if (1) {
	x0 = 0.04
	x1 = x0 + 0.04
	y0 = 0.62
	y1 = y0 + 0.15
	set obj 1 rect from graph x0, y0 to graph x1, y1 fs solid TRANS border lw 2 fc rgb "red" front
	set label "in Local SSD" at graph x1, (y0+y1)/2.0 offset 0.7, 0 tc rgb "red"

	y2 = y1 + 0.15
	set obj 2 rect from graph x0, y1 to graph x1, y2 fs solid TRANS border lw 2 fc rgb "blue" front
	set label "in EBS Mag" at graph x1, (y1+y2)/2.0 offset 0.7, 0 tc rgb "blue"
}

plot \
IN_FN_M u 1:(0):1:2:(0):16 w boxxyerrorbars fs solid TRANS noborder lc rgb "blue" not, \
""      u 1:(0):1:2:(0):12 w boxxyerrorbars fs solid TRANS noborder lc rgb "red"  not, \
""      u 1:12:3:(0)         w vectors nohead lc rgb "red" not, \
""      u 2:12:(0):($17-$12) w vectors nohead lc rgb "red" not, \
""      u 1:16:3:(0)         w vectors nohead lc rgb "blue" not, \
""      u 2:16:(0):($21-$16) w vectors nohead lc rgb "blue" not, \

# Tried legend. Didn't like it much.
#""      u (0):(0):(0):(0):(0):(0) w boxxyerrorbars fs solid TRANS border   lc rgb "blue" t "SSTables in EBS Mag", \
#""      u (0):(0):(0):(0):(0):(0) w boxxyerrorbars fs solid TRANS border   lc rgb "red"  t "SSTables in Local SSD", \

# Tried boxxyerrorbars, but too many, distracting vertical lines
#plot IN_FN_M u 1:(0):1:2:(0):16 w boxxyerrorbars fs solid 0.0 lc rgb "red" t "RocksDB on Local SSD"

#IN_FN_M u 1:(0):1:2:(0):20 w boxxyerrorbars fs solid 0.0 lc rgb "blue" t "Mutant with Local SSD and EBS Mag", \

# boxxyerrorbars: x y xlow xhigh ylow yhigh
