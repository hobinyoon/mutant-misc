# Tested with gnuplot 4.6 patchlevel 6

FN_IN_SST_INFO = system("echo $FN_IN_SST_INFO")
FN_IN_SST_LEVEL_INFO = system("echo $FN_IN_SST_LEVEL_INFO")
FN_IN_SST_HEAT = system("echo $FN_IN_SST_HEAT")
FN_OUT = system("echo $FN_OUT")

set print "-"
print sprintf("FN_IN_SST_INFO=%s", FN_IN_SST_INFO)
print sprintf("FN_IN_SST_LEVEL_INFO=%s", FN_IN_SST_LEVEL_INFO)
print sprintf("FN_IN_SST_HEAT=%s", FN_IN_SST_HEAT)

#----------------------------------------------------------
# Get data range
set xdata time
set timefmt "%y%m%d-%H%M%S"
set format x "%H:%M"

set terminal unknown
plot \
FN_IN_SST_INFO u 4:12:4:5:12:($12 + $6) w boxxyerrorbars not
X_MIN=GPVAL_DATA_X_MIN
X_MAX=GPVAL_DATA_X_MAX
Y_MIN=GPVAL_DATA_Y_MIN
Y_MAX=GPVAL_DATA_Y_MAX
print sprintf("X_MIN=%d X_MAX=%d Y_MIN=%d Y_MAX=%d", X_MIN, X_MAX, Y_MIN, Y_MAX)

plot \
FN_IN_SST_HEAT u 0:8 w p
READS_PER_SEC_MAX=GPVAL_DATA_Y_MAX
print sprintf("READS_PER_SEC_MAX=%f", READS_PER_SEC_MAX)

#----------------------------------------------------------
set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

#set grid xtics mxtics back lc rgb "#808080"
#set grid back
set border front lc rgb "#808080"
set xtics nomirror scale 0.5,0.25 out tc rgb "black" autofreq 0,20 * 60
set nomxtics

# No ytics
unset ytics
set ytics scale 0,0 format ""

set tics front

set ylabel "SSTables\n(grouped by levels)"
set xlabel "Time"

set xrange[X_MIN:X_MAX]
set yrange[Y_MIN:Y_MAX]

# Legend
#   x0, x1, ... are from left to right
#   y0, y1, ... are from top to bottom
#   x_width: width of the function part
x0=0.05
x1=x0 + 0.04
y0=0.96
x_width=0.15
x2=x1+x_width

y_height=0.25

# Play with this if you see horizontal stripes
y_overlap=0.95
y_unit = y_height / 256.0

y1=y0 - y_unit * (256 + y_overlap)

#set object 1 rect from graph x0, graph y1 to graph x1 + 0.2, graph y0 fs transparent solid noborder fc rgb "#0000FF" front

#color0(i)=256*256 * 255 + 256 * (255 * (1.0 - i)) + (255 * (1.0 - i))

# http://stackoverflow.com/questions/12875486/what-is-the-algorithm-to-create-colors-for-a-heatmap
# 0    red    #FF0000 16711680
# 0.25 yellow #FFFF00 16776960
# 0.5  green  #00FF00 65280
# 0.75 cyan   #00FFFF 65535
# 1    blue   #0000FF 255
#color1(i)=(i < 0.25 ? (16711680 + int((i / 0.25) * 255.9999999) * 256) : \
#i < 0.5  ? (65280 + int((1 - (i - 0.25) / 0.25) * 255.9999999) * 256 * 256) : \
#i < 0.75 ? (65280 + int((i - 0.50) / 0.25 * 255.9999999)) : \
#           (255 + int((1 - (i - 0.75) / 0.25) * 255.9999999) * 256))
#color0(i)=color1(1.0-i)

# Use only red and blue
# 1    red    #FF0000 16711680
# 0.75 white  #FFFFFF 16777215
# 0    blue   #0000FF 255
#color0(i)=(i < 0.25 ? (int(i / 0.75 * 255.9999999) * 256 * 256 + int(i / 0.75 * 255.9999999) * 256 + 255) : \
#i < 0.75 ? (int((i - 0.25) / 0.75 * 255.9999999) * 256 * 256 + int((0.75 - i) / 0.75 * 255.9999999)) : \
#(int((i - 0.25) / 0.75 * 255.9999999) * 256 * 256))

#color0(i)=(16777215)

#color0(i)=(i < 0.75 ? (int(floor(255)) * 256 * 256 + int(floor(255.9999)) * 256 + 255) : \
#16777215)

#color0(i)=(i < 0.75 ? (255 * 256 * 256 + 255 * 256 + 255) : \
#16777215)

#                  R |      G |      B
#------------------------------------
# 0     blue      00 |     00 |     FF
# 0.25        1/3 FF | 1/3 FF |     FF
#
# 0.50            FF | 2/3 FF |     FF
#
# 0.75            FF | 1/3 FF | 1/3 FF
# 1      red      FF |     00 |     00
#
#color0(i)=(i < 0.25 ? (int(i / 0.75 * 255.9999999)                  * 256 * 256 + int(i / 0.75 * 255.9999999) * 256 + 255) : \
#           i < 0.50 ? (int((8.0/3*(i-1.0/4) + 1.0/3) * 255.9999999) * 256 * 256 + int(i / 0.75 * 255.9999999) * 256 + 255) : \
#16777215)

color0(i)=( \
i < 0.5 ? (int(i / 0.5 * 255.9999999) * 256 * 256 + int(i         / 0.5 * 255.9999999) * 256 +                                255) : \
          (                       255 * 256 * 256 + int((1.0 - i) / 0.5 * 255.9999999) * 256 + int((1.0 - i) / 0.5 * 255.9999999)) \
)

do for [i=0:255] {
	set object (i+100) rect from graph x0, graph y0 - y_unit * (i+1+y_overlap) \
	to graph x1, graph y0 - y_unit * i \
	fs solid 1.0 noborder fc rgb color0((255 - i) / 255.0) lw 0.1 front
}

set object rect from graph x0, graph y0 - y_unit * (255+1+y_overlap) \
to graph x1, graph y0 - y_unit * (0) \
fs transparent solid 0.0 border fc rgb "#808080" front

# Legend tics
#max_plotted=0
#do for [i=-1:5] {
#	if (i == -1) {
#		v=0
#	} else {
#		v=1000 * 2**i
#	}
#
#	if (READS_PER_SEC_MAX <= v) {
#		if (max_plotted == 0) {
#			v=READS_PER_SEC_MAX
#		}
#	}
#
#	print sprintf("v =%f", v)
#	v1=(v / READS_PER_SEC_MAX) ** 0.65
#	print sprintf("v1=%f", v1)
#	y=y1 + (y0 - y1) * v1
#
#	if (v < READS_PER_SEC_MAX) {
#		set label sprintf("%d", v) at graph x1, graph y offset 0.5,0 font ",9"
#		set arrow from graph x1, graph y to graph x1 + 0.01, graph y nohead lc rgb "#808080"
#	} else {
#		if (max_plotted == 0) {
#			set label sprintf("%d", v) at graph x1, graph y offset 0.5,0 font ",9"
#			set arrow from graph x0, graph y to graph x1 + 0.01, graph y nohead lc rgb "#808080" front
#			max_plotted=1
#		} else {
#		}
#	}
#}

set sample 1000

# Legend function
{
	x_w=X_MAX-X_MIN
	y_h=Y_MAX-Y_MIN

	x2=x1+0.22

	x1 = x1*x_w + X_MIN
	x2 = x2*x_w + X_MIN
	x0 = x0*x_w + X_MIN

	y0 = y0*y_h + Y_MIN
	y1 = y1*y_h + Y_MIN

	x_w = x2-x1
	y_h = y0-y1

	# Verify the coordinates
	#set obj circle at x1,y0 size 10 fs solid fc rgb "black"
	#set obj circle at x2,y0 size 10 fs solid fc rgb "black"
	#set obj circle at x1,y1 size 10 fs solid fc rgb "black"

	set label "Reads/sec/MB" at (x0+x2)/2, y1 center offset 0,-1.3 font ",9"

	# xtics
	set arrow from x1,y1 to x2,y1 nohead lc rgb "#808080"
	set arrow from x1,y1 to x1,y1-0.05*y_h nohead lc rgb "#808080"
	set arrow from x2,y1 to x2,y1-0.05*y_h nohead lc rgb "#808080"
	set label "0"                              at x1,y1 center offset 0,-0.6 font ",9"
	set label sprintf("%.2f", READS_PER_SEC_MAX) at x2,y1 center offset 0,-0.6 font ",9"

	# border
	set arrow from x1,y0 to x2,y0 nohead lc rgb "#808080"
	set arrow from x2,y0 to x2,y1 nohead lc rgb "#808080"

	# Linear
	#y - y1 = y_h/x_w * (x-x1)
	#f(x) = y_h/x_w * (x-x1) + y1

	# Power
	#(y-y1)/y_h = ((x-x1)/x_w)**0.65
	#f(x) = ((x-x1)/x_w)**0.65 * y_h + y1

	# Power mirrored by x and y axis and panned
	a = 10
	#v = - math.pow(-v+1, a) + 1
	#(y-y1)/y_h = - math.pow(-(v-x1)/x_w + 1, a) + 1
	#(y-y1)/y_h = - (-(v-x1)/x_w + 1) ** a + 1
	#y = (- (-(v-x1)/x_w + 1) ** a + 1) * y_h + y1
	f(x) = (- (-(x-x1)/x_w + 1) ** a + 1) * y_h + y1

	legend_f(x) = ( x < x1 ? 1/0 : \
		x2 < x ? 1/0 : \
		f(x) )
}

plot \
FN_IN_SST_INFO u 4:12:4:5:12:($12 + $6) w boxxyerrorbars fs solid noborder lc rgb "#0000FF" not, \
FN_IN_SST_HEAT u 3:6:3:4:6:7:9 w boxxyerrorbars fs solid lc rgb variable not, \
FN_IN_SST_INFO u 4:12:4:5:12:($12 + $6) w boxxyerrorbars lc rgb "#808080" not, \
FN_IN_SST_LEVEL_INFO u (X_MIN):2:1 w labels offset -1,0 not, \
FN_IN_SST_LEVEL_INFO u (X_MIN):($3 == 0 ? 1/0 : $3):(X_MAX - X_MIN):(0) w vectors nohead lt 0 lw 3 lc rgb "black" not, \
FN_IN_SST_INFO u 4:($12+($6/2)):1 w labels left font ",3" not, \
legend_f(x) lc rgb "black" not

# Heat (access frequencies) color
#FN_IN_SST_HEAT u 3:6:3:4:6:7:9 w boxxyerrorbars fs solid lc rgb variable not, \

# Bounding box representing SSTable creation and deletion times
#   I wanted a super thin bounding box like lw 0.2, but the box is a bit inside
#   the color strips.
#FN_IN_SST_INFO u 4:12:4:5:12:($12 + $6) w boxxyerrorbars lc rgb "#808080" not, \

# Dots representing number of reads. Not used any more.
#FN_IN_SST_NUM_READS u 2:4 w p pt 7 pointsize 0.05 lc rgb "red" not, \

# SstGen
#FN_IN_SST_INFO u 4:($12+($6/2)):1 w labels left font ",3" not, \

# Desc. Not showing for now. Some are too long.
#FN_IN_SST_INFO u 4:($12+($6/2)):13 w labels left font ",3" not, \

# xerrorbars:     x y xlow xhigh
# boxxyerrorbars: x y xlow xhigh ylow yhigh
