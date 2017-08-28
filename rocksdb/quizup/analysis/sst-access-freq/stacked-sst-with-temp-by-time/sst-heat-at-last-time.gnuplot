# Tested with gnuplot 4.6 patchlevel 4

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
print sprintf("FN_IN=%s", FN_IN)
print sprintf("FN_OUT=%s", FN_OUT)

#----------------------------------------------------------
# Get data range
set terminal unknown
plot FN_IN u 0:3:(0.8) w boxes
X_MIN=GPVAL_DATA_X_MIN
X_MAX=GPVAL_DATA_X_MAX
#----------------------------------------------------------

poster=1

if (poster == 1) {
	set terminal pdfcairo enhanced size 1.8in, (1.8*0.85)in
} else {
	set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
}
set output FN_OUT

set border front lc rgb "#808080" front
set grid xtics ytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" #autofreq 0,2*60*60
set ytics nomirror tc rgb "black" #autofreq 0,2*60*60
set tics front

set xlabel "SSTables"
set ylabel "Temperature"

set xrange[X_MIN:X_MAX]

#set logscale y

plot \
FN_IN u 0:3:(0.7) w lp pt 7 pointsize 0.15 lw 2 lc rgb "red" not

# I can stack some of these!

#FN_IN u 0:3:(0.7) w boxes fs solid noborder lc rgb "red" not

# boxes: x y x_width
