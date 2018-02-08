# Tested with gnuplot 4.6 patchlevel 4

FN_IN_BOXES = system("echo $FN_IN_BOXES")
FN_IN_LEVEL_INFO = system("echo $FN_IN_LEVEL_INFO")
MAX_PLOT_HEIGHT = system("echo $MAX_PLOT_HEIGHT") + 0
FN_OUT = system("echo $FN_OUT")

set print "-"
print sprintf("MAX_PLOT_HEIGHT=%d", MAX_PLOT_HEIGHT)

#----------------------------------------------------------
# Get data range
set terminal unknown
plot FN_IN_BOXES u 7:9:7:8:9:($9 + 1) w boxxyerrorbars
X_MIN=GPVAL_DATA_X_MIN + 0.0
X_MAX=GPVAL_DATA_X_MAX + 0.0
Y_MIN=GPVAL_DATA_Y_MIN
Y_MAX=GPVAL_DATA_Y_MAX
# %f for big numbers, like 64-bit numbers. %d doesn't give you a correct
# representation of numbers
print sprintf("X_MIN=%.0f X_MAX=%.0f Y_MIN=%d Y_MAX=%d", X_MIN, X_MAX, Y_MIN, Y_MAX)
#----------------------------------------------------------

poster = 0

if (poster == 1) {
	set terminal pdfcairo enhanced size 1.7in, (1.7*0.85)in
} else {
	set terminal pdfcairo enhanced size 1.9in, (1.9*0.85)in
}
set output FN_OUT

set noborder
set noytics

set tmargin screen 1.0
set bmargin screen 0.23
set lmargin screen 0.01
set rmargin screen 0.97

# Normalized keyspace
set xlabel "Keyspace" offset 2, 0.7

set xtics nomirror out format "%.0f" autofreq 0, 1 offset 0,-0.2
#set ytics nomirror scale 0, 0 format "%.0f" autofreq 0, 1

# Origin at the top left
set yrange [:MAX_PLOT_HEIGHT] reverse

# A bit stuck out to the left
set xrange [-0.2:1]

# Keyspace bar
y0 = MAX_PLOT_HEIGHT + 0.2
set arrow from 0, y0 to 1, y0 nohead
set arrow from 0, y0-0.2 to 0, y0+0.2 nohead
set arrow from 1, y0-0.2 to 1, y0+0.2 nohead

# Normalize x to [0, 1]
n(x)=1.0*(x-X_MIN)/(X_MAX-X_MIN)

# Labels with different colors. It won't be very visible. There are quite a few rectangles smaller than the labels.

# Labels with outline
if (1) {
	# (sst_gen and level)-based filtering
	n0(sst_gen, l, x)=(sst_gen<=20 || l==0) ? n(x) : 1/0
	n1(sst_gen, l, x)=(sst_gen> 20 && l!=0) ? n(x) : 1/0

  F0 = ",10"
  o0x=0.20
  o0y=0.18
  o0x_=o0x*0.1
  o0y_=o0y*0.1

  F1 = ",10"
  o1x=0.15
  o1y=0.13
  o1x_=o1x*0.1
  o1y_=o1y*0.1

  plot \
  FN_IN_BOXES u (n($7)):9:(n($7)):(n($8)):9:10:5 w boxxyerrorbars fs solid noborder lc rgb variable not, \
	FN_IN_BOXES u (n($7)):9:(n($7)):(n($8)):9:10 w boxxyerrorbars lc rgb "#D0D0D0" lw 3 not, \
	FN_IN_LEVEL_INFO u (-0.15):2:(1.2):(0) w vectors nohead lt 0 lw 4 lc rgb "black" not, \
	FN_IN_LEVEL_INFO u (-0.15):1:(sprintf("L%d", $0)) w labels left tc rgb "black" not, \
  \
  for [i=-10:10] FN_IN_BOXES u (n0($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset o0x_*i, o0y tc rgb "while" font F0 not, \
  for [i=-10:10] FN_IN_BOXES u (n0($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset o0x_*i,-o0y tc rgb "while" font F0 not, \
  for [i=-10:10] FN_IN_BOXES u (n0($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset  o0x,o0y_*i tc rgb "while" font F0 not, \
  for [i=-10:10] FN_IN_BOXES u (n0($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset -o0x,o0y_*i tc rgb "while" font F0 not, \
  FN_IN_BOXES u (n0($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center font F0 not, \
  \
	for [i=-10:10] FN_IN_BOXES u (n1($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset o1x_*i, o1y rotate by 90 tc rgb "while" font F1 not, \
	for [i=-10:10] FN_IN_BOXES u (n1($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset o1x_*i,-o1y rotate by 90 tc rgb "while" font F1 not, \
	for [i=-10:10] FN_IN_BOXES u (n1($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset  o1x,o1y_*i rotate by 90 tc rgb "while" font F1 not, \
	for [i=-10:10] FN_IN_BOXES u (n1($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center offset -o1x,o1y_*i rotate by 90 tc rgb "while" font F1 not, \
	FN_IN_BOXES u (n1($1, $2, $7 + ($8 - $7)/2.0)):(($9+$10)/2.0):1 w labels center rotate by 90 font F1 not

}

# With SST gen labels for illustration
#FN_IN_BOXES u (n($7 + ($8 - $7)/2.0)):10:1 w labels rotate by 90 not, \

# boxxyerrorbars: x y xlow xhigh ylow yhigh
