# Tested with gnuplot 4.6 patchlevel 4

FN_IN_HEATMAP = system("echo $FN_IN_HEATMAP")
FN_IN_VERTICAL_LINES = system("echo $FN_IN_VERTICAL_LINES")
FN_OUT = system("echo $FN_OUT")

set print "-"
print sprintf("FN_IN_HEATMAP=%s", FN_IN_HEATMAP)
print sprintf("FN_IN_VERTICAL_LINES=%s", FN_IN_VERTICAL_LINES)
print sprintf("FN_OUT=%s", FN_OUT)

# Get data range
if (1) {
	set terminal unknown
	plot FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
}

poster=0

if (poster == 1) {
	set terminal pdfcairo enhanced size 3.4in, (2.3*0.60)in
} else {
	set terminal pdfcairo enhanced size 2.8in, 1.8in
}
set output FN_OUT

set border front lc rgb "#808080" front
set xtics out nomirror tc rgb "black" offset 0,0.2 ( \
"0" 0, \
"2" 2*24*3600, \
"4" 4*24*3600, \
"6" 6*24*3600, \
"8" 8*24*3600, \
"10" 10*24*3600, \
"12" 12*24*3600, \
"14" 14*24*3600, \
"16" 16*24*3600 \
)
set mxtics 2
set tics front
set noytics
set nomytics

set xlabel "Time (day)" offset 0,0.3
set ylabel "SSTables" offset -0.5,0
# SSTables stacked, sorted by temperature, total-size normalized

# Legend
if (1) {
	# x0, x1, ... are from left to right
	# y0, y1, ... are from top to bottom
	# x_width: width of the function part
	x0=0.83
	x1=x0 + 0.03
	y0=0.928
	x_width=0.15
	x2=x1+x_width

	y_height=0.7065

	# Play with this if you see horizontal stripes
	y_overlap=0.95
	y_unit = y_height / 256.0

	y1=y0 - y_unit * (256 + y_overlap)

	color0(i)=( \
	i < 0.5 ? (int(i / 0.5 * 255.9999999) * 256 * 256 + int(i         / 0.5 * 255.9999999) * 256 +                                255) : \
						(                       255 * 256 * 256 + int((1.0 - i) / 0.5 * 255.9999999) * 256 + int((1.0 - i) / 0.5 * 255.9999999)) \
	)

	do for [i=0:255] {
		set object (i+100) rect from screen x0, screen y0 - y_unit * (i+1+y_overlap) \
		to screen x1, screen y0 - y_unit * i \
		fs solid 1.0 noborder fc rgb color0((255 - i) / 255.0) lw 0.1 front
	}

	set object rect from screen x0, screen y0 - y_unit * (255+1+y_overlap) \
	to screen x1, screen y0 - y_unit * (0) \
	fs transparent solid 0.0 border fc rgb "#808080" front

	y_t=y0 - y_unit * (0)
	y_b=y0 - y_unit * (255+1+y_overlap)

	a=10
	heat_curve(v)=log10(v)/3.8 + 1

	temps = "0.001 0.01 0.1 1"
	temp_labels = "10^{-3} 10^{-2} 10^{-1} 1"
	do for [i=1:words(temps)] {
		temp = word(temps, i) * 1.0
		y2=y_b + (y_t - y_b) * heat_curve(temp)
		set arrow from screen x1, screen y2 to screen x1+0.01, screen y2 nohead lc rgb "black" front
		set label word(temp_labels, i) at screen x1, screen y2 left offset 1,0 tc rgb "black" font ",10" front
	}

	y2=y_b - 0.1
	set label "Access\nfreq." at screen x1, screen y2 center offset 0.5,0.5 tc rgb "black" front

	set size 0.85,1
}

set xrange[X_MIN:X_MAX]

# Origin at the top left
set yrange [:] reverse

vertical_lines_only=0
if (vertical_lines_only == 1) {
	plot \
	FN_IN_HEATMAP u 3:5:3:4:5:6:9 w boxxyerrorbars fs solid lc rgb variable not, \
	FN_IN_VERTICAL_LINES u 1:(0):(0):(1) w vectors nohead lc rgb "white" lw 3 not
} else {
	plot \
	FN_IN_HEATMAP u 3:5:3:4:5:6:9 w boxxyerrorbars fs solid lc rgb variable not, \
	FN_IN_HEATMAP u 3:5:3:4:5:6:9 w boxxyerrorbars lc rgb "white" lw 1 not
}

#FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars lc rgb "white" lw 0.5 not, \

# Sst gen
#FN_IN_HEATMAP u 3:5:1 w labels not font ",4"

# Sst bounding box, individual, not pretty
#FN_IN_HEATMAP u 3:5:3:4:5:6:8 w boxxyerrorbars lc rgb "white" lt 0 not, \

# xerrorbars:     x y xlow xhigh
# boxxyerrorbars: x y xlow xhigh ylow yhigh
