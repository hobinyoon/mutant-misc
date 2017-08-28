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
	set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
}
set output FN_OUT

set noborder
set noytics

# Normalized keyspace
set xlabel "Keyspace" offset 2, 0.7

set xtics nomirror out format "%.0f" autofreq 0, 1
#set ytics nomirror scale 0, 0 format "%.0f" autofreq 0, 1

# Origin at the top left
set yrange [:MAX_PLOT_HEIGHT] reverse

# A bit stuck out to the left
set xrange [-0.2:1]

# Keyspace bar
set arrow from 0, MAX_PLOT_HEIGHT to 1, MAX_PLOT_HEIGHT nohead
set arrow from 0, MAX_PLOT_HEIGHT-0.2 to 0, MAX_PLOT_HEIGHT+0.2 nohead
set arrow from 1, MAX_PLOT_HEIGHT-0.2 to 1, MAX_PLOT_HEIGHT+0.2 nohead

# Normalize x to [0, 1]
n(x)=1.0*(x-X_MIN)/(X_MAX-X_MIN)

plot \
FN_IN_BOXES u (n($7)):9:(n($7)):(n($8)):9:($9 + 1):5 w boxxyerrorbars fs solid noborder lc rgb variable not, \
FN_IN_BOXES u (n($7)):9:(n($7)):(n($8)):9:($9 + 1) w boxxyerrorbars lc rgb "#A0A0A0" lw 1 not, \
FN_IN_LEVEL_INFO u (-0.2):2:(1.2):(0) w vectors nohead lt 0 lw 4 lc rgb "black" not, \
FN_IN_LEVEL_INFO u (-0.2):1:(sprintf("L%d", $0)) w labels left tc rgb "black" not, \

# With SST gen labels for illustration
#FN_IN_BOXES u (n($7 + ($8 - $7)/2.0)):($9+0.5):1 w labels rotate by 90 not, \

# boxxyerrorbars: x y xlow xhigh ylow yhigh
