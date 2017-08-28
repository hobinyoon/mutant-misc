#!/usr/bin/gnuplot

FN_OUT = "heatmap-legend-only.pdf"

set terminal pdfcairo enhanced size 1.9in, 1.95in
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
	x0=0.90
	x1=x0 + 0.06
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
		set arrow from screen x0, screen y2 to screen x0-0.02, screen y2 nohead lc rgb "#808080" front
		set label word(temp_labels, i) at screen x0-0.08, screen y2 right offset 1,0 tc rgb "black" front
		#set label word(temp_labels, i) at screen x0-0.08, screen y2 right offset 1,0 tc rgb "black" font ",10" front
	}

	y2=y_b - 0.1
	x3 = x1 - 0.05
	set label "Access\nfreq." at screen x3, screen y2 center offset 0.5,0.5 tc rgb "black" front

	set size 0.83,1
}

plot "-" using 1:2
1 1
2 2
e
