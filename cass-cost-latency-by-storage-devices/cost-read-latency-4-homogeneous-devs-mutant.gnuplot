#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN="data-cost-read-lat-4-homogeneous-devs-mutant"
FN_OUT="cass-cost-read-lat-4-homogeneous-devs-mutant.pdf"

ymir_style=0

if (ymir_style) {
	set terminal pdfcairo enhanced font "Gill Sans, 21" linewidth 4 rounded size 5,3
} else {
	set terminal pdfcairo enhanced size 3.0in, (2.8*0.75)in
}
set output FN_OUT

set print "-" 

if (ymir_style) {
	set style line 80 lt rgb "black"
	set style line 81 lt 0  # dashed
	set style line 81 lt rgb "#808080"  # grey

	set grid back linestyle 81
	set border 3 back linestyle 80
	set xtics nomirror
	set ytics nomirror
	set size 1,1
} else {
	set border lc rgb "#808080" front
	#set grid xtics ytics back lc rgb "#800880" front
	set xtics nomirror scale 1, 0.5 tc rgb "black"
	set ytics nomirror scale 1, 0.5 tc rgb "black"
	set mxtics
	set mytics
}

set tics front

set xlabel "Cost (K$)"
set ylabel "Read latency (ms)" offset 1.9,0

LINE_WIDTH=4

# Legend: error bar
if (1) {
	x_c=0.75
	y_t=0.92
	y_b=y_t-0.20
	LC="#404040"
	set arrow from graph x_c, y_b to graph x_c, y_t nohead lw LINE_WIDTH lc rgb LC front
	x_l=x_c-0.015
	x_r=x_c+0.015
	set arrow from graph x_l, y_t to graph x_r, y_t nohead lw LINE_WIDTH lc rgb LC front
	set arrow from graph x_l, y_b to graph x_r, y_b nohead lw LINE_WIDTH lc rgb LC front
	y3=(y_t+y_b)/2
	set object circle at graph x_c, y3 size screen 0.010 fs solid noborder fc rgb LC front
	set label "99%" at graph x_c, y_t offset 0.9,0 front
	set label "Avg" at graph x_c, y3  offset 0.9,0 front
	set label "1%"  at graph x_c, y_b offset 0.9,0 front
}

color1(i)=int((1-i) * 255.9999999) * 256 * 256 + 255 * 256 + int((1-i) * 255.9999999)
# 0.61 to make it the color lighter. changes the domain from [0:1] to [0:0.61]
color0(i)=color1((i**2.0) * 0.61)

# Legend: heat color
if (1) {
	# x0, x1, ... are from left to right
	# y0, y1, ... are from top to bottom
	# x_width: width of the function part
	x0=0.80
	x_width=0.03
	x1=x0 + x_width
	y0=0.932

	y_height=0.732

	# Play with this if you see horizontal stripes
	y_overlap=0.95
	y_unit = y_height / 256.0

	y1=y0 - y_unit * (256 + y_overlap)

	do for [i=0:255] {
		set object (i+100) rect from screen x0, screen y0 - y_unit * (i+1+y_overlap) \
		to screen x1, screen y0 - y_unit * i \
		fs solid 1.0 noborder fc rgb color0(i / 255.0) lw 0.1 front
	}

	set object rect from screen x0, screen y0 - y_unit * (255+1+y_overlap) \
	to screen x1, screen y0 - y_unit * (0) \
	fs transparent solid 0.0 border fc rgb "#808080" front

	y_t=y0 - y_unit * (0)
	y_b=y0 - y_unit * (255+1+y_overlap)

	do for [i=1:9] {
		heat = i/10.0
		y2=y_t + (y_b - y_t) * heat
		set arrow from screen x0, screen y2 to screen x1, screen y2 nohead lt 0 lw 4 lc rgb "#808080" front
	}

	# Latency per dollar (ms / $ / year)
	lpd_min=5.0/4000

	# TODO: finish the calculation
	# When you jump 5 notches along the y-axis, latency increaes by 100x: 9 notches -> 
	# When you jump 2 notches along the x-axis, latency increaes by 8x

	ltd_min=5.0*400
	ltd_max=50000.0*2000
	x2=x1+0.02
	do for [i=0:5] {
		heat = 2.0*i/10.0
		y2=y_t + (y_b - y_t) * heat
		set label (sprintf("%.1f", heat)) at screen x2, screen y2 tc rgb "black" front
	}

	x3=x2+0.11
	y2=(y0 + y1) / 2.0
	#set label "Cost\nefficiency" at screen x1, screen y2 center offset 0.8,0 tc rgb "black" front
	set label "Latency times dollar (ms $)" at screen x3, screen y2 center rotate by 90 tc rgb "black" front

	# Make the plot narrower to accomodate the heatmap legend bar
	set size 0.84,1
}


#colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

# http://stackoverflow.com/questions/12427704/vary-point-color-based-on-column-value-for-multiple-data-blocks-gnuplot
set palette model RGB defined (\
  0 "#0000FF" \
, 1 "#008000" \
, 2 "#91553D" \
, 3 "#FF0000" \
, 4 "#6B3FA0" \
)
unset colorbox

set xrange[0.25:15]
set yrange[4:1500]

f0(x, a)=a/x
f1(x, a)=a/x > 1500 ? 1500 : f0(x, a)

#set samples 1000

set logscale xy

#set style fill transparent solid 0.5 noborder

plot \
for [i=1:99] f1(x, 2.7**((9.0-1.0)*(99.0-i)/(99.0-1.0)+1.0)) with filledcurve x1 fs solid 1.0 lc rgb color0((i-1.0)/(99.0-1.0)) not, \
for [i=1:9] f0(x, 2.7**i) with l lc rgb "#A0A0A0" lt 0 lw 5 not, \
FN_IN u ($2/1000):($3/1000):($4/1000):($5/1000):0 w yerrorbars pt 7 pointsize 0.5 lw LINE_WIDTH palette not, \
FN_IN u ($2/1000):($3/1000):($0 < 3  ? strcol(1) : ""):0 w labels left  offset  0.7,0 font "Arial-Bold" tc palette not, \
FN_IN u ($2/1000):($3/1000):($0 >= 3 ? strcol(1) : ""):0 w labels right offset -0.7,0 font "Arial-Bold" tc palette not

# You can't get the output file size here. It returns 0. The file must not be closed yet.
#   cmd="wc -c < " . FN_OUT
#   system(cmd)
print sprintf("Created %s", FN_OUT)
