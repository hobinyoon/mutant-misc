# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
print sprintf("FN_IN=%s", FN_IN)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080" back

set logscale xy

plot \
FN_IN every 100::0 u 0:2 w lp pt 7 pointsize 0.2 not

#----------------------------------------------------------
# Get data range
#set terminal unknown
#set xdata time
#set timefmt "%y%m%d-%H%M%S"
#plot FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars
#X_MIN=GPVAL_DATA_X_MIN
#X_MAX=GPVAL_DATA_X_MAX
#----------------------------------------------------------

#poster=1
#
#if (poster == 1) {
#	# Wider one for poster
#	set terminal pdfcairo enhanced size 3.4in, (2.3*0.60)in
#} else {
#	set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
#}
#set output FN_OUT
#
##set rmargin 0.90
#
#set border front lc rgb "#808080" front
##set grid ytics mytics back lc rgb "#808080"
#set xtics out nomirror tc rgb "black" autofreq 0,2*60*60 offset 0,0.2
#set mxtics 2
#set tics front
#set noytics
#set nomytics
#
#set xlabel "Time (hour)" offset 0,0.7
#set ylabel "SSTables" offset 0,0
## SSTables stacked, sorted by temperature, total-size normalized
#
## Legend
#if (1) {
#	# x0, x1, ... are from left to right
#	# y0, y1, ... are from top to bottom
#	# x_width: width of the function part
#	x0=0.83
#	x1=x0 + 0.03
#	y0=0.90
#	x_width=0.15
#	x2=x1+x_width
#
#	y_height=0.63
#
#	# Play with this if you see horizontal stripes
#	y_overlap=0.95
#	y_unit = y_height / 256.0
#
#	y1=y0 - y_unit * (256 + y_overlap)
#
#	color0(i)=( \
#	i < 0.5 ? (int(i / 0.5 * 255.9999999) * 256 * 256 + int(i         / 0.5 * 255.9999999) * 256 +                                255) : \
#						(                       255 * 256 * 256 + int((1.0 - i) / 0.5 * 255.9999999) * 256 + int((1.0 - i) / 0.5 * 255.9999999)) \
#	)
#
#	do for [i=0:255] {
#		set object (i+100) rect from screen x0, screen y0 - y_unit * (i+1+y_overlap) \
#		to screen x1, screen y0 - y_unit * i \
#		fs solid 1.0 noborder fc rgb color0((255 - i) / 255.0) lw 0.1 front
#	}
#
#	set object rect from screen x0, screen y0 - y_unit * (255+1+y_overlap) \
#	to screen x1, screen y0 - y_unit * (0) \
#	fs transparent solid 0.0 border fc rgb "#808080" front
#
#	y_t=y0 - y_unit * (0)
#	y_b=y0 - y_unit * (255+1+y_overlap)
#
#	a=10
#	heat_curve(v)=1 - (-1 * ((-v+1)**a) + 1)
#
#	heats = "0 2 4 8 16 1000"
#	do for [i=1:words(heats)] {
#		heat = word(heats, i) * 1.0
#		if (heat >= HEAT_MAX) {
#			heat = HEAT_MAX
#		}
#		y2=y_t + (y_b - y_t) * heat_curve(heat/HEAT_MAX)
#		set arrow from screen x1, screen y2 to screen x1+0.01, screen y2 nohead lc rgb "#808080" front
#		set label (sprintf("%.1f", heat)) at screen x1, screen y2 right offset 4.2,0 tc rgb "black" font ",10" front
#	}
#
#	y2=y_b - 0.1
#	set label "accesses /\nsec / MiB" at screen x1, screen y2 center offset 2.0,0 tc rgb "black" front
#
#	set size 0.85,1
#}
#
##set format x "%H:%M"
#set format x "%1H"
#
#set xrange[X_MIN:X_MAX]
#
## Origin at the top left
#set yrange [:] reverse
#
#vertical_lines_only=1
#if (vertical_lines_only == 1) {
#	plot \
#	FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars fs solid lc rgb variable not, \
#	FN_IN_VERTICAL_LINES u 1:(0):(0):(1) w vectors nohead lc rgb "white" not
#} else {
#	plot \
#	FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars fs solid lc rgb variable not, \
#	FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars lc rgb "white" lw 0.5 not
#}

#FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars lc rgb "white" lw 0.5 not, \

# Sst gen
#FN_IN_HEATMAP u 3:5:1 w labels not font ",4"

# Sst bounding box, individual, not pretty
#FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars lc rgb "white" lt 0 not, \

# xerrorbars:     x y xlow xhigh
# boxxyerrorbars: x y xlow xhigh ylow yhigh
