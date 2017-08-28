# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
LEVEL = system("echo $LEVEL") + 0
AGE_DELETED = system("echo $AGE_DELETED") + 0.0
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)
#print sprintf("AGE_DELETED=%f", AGE_DELETED)

set border front lc rgb "#808080" back
set grid xtics ytics back lc rgb "#808080"

if (LEVEL == 0) {
	# x values in hours
	set xtics nomirror tc rgb "black" format "%.0fh" autofreq 0,1
	x_val(x)=x/3600.0
} else {
if (LEVEL == 1) {
	# x values in hours
	set xtics nomirror tc rgb "black" format "%.0fh" autofreq 0,1
	x_val(x)=x/3600.0
} else {
if (LEVEL == 2) {
	# x values in days
	set xtics nomirror tc rgb "black" format "%.0fd" autofreq 0,1
	x_val(x)=x/24.0/3600.0
} } }

set ytics nomirror tc rgb "black"
set tics back

# Get data range
if (1) {
	set terminal unknown
	plot IN_FN u (x_val($1)):4 w p
	#Y_MAX=GPVAL_DATA_Y_MAX
	Y_MAX=GPVAL_Y_MAX
}

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output OUT_FN

set xlabel "SSTables age"
set ylabel "Access freq (cnt / 64MB / sec)"

#set logscale y
set yrange[0:]

set style fill transparent solid 0.1 border

set arrow from (x_val(AGE_DELETED)), 0 to (x_val(AGE_DELETED)), Y_MAX nohead lt 0 lc rgb "blue" lw 5
set label "deleted" at (x_val(AGE_DELETED)), Y_MAX center offset 0,0.7 tc rgb "blue"

plot \
IN_FN u (x_val($1)):(0):(x_val($1)):(x_val($2)):(0):4 w boxxyerrorbar not, \

# The linepoint connecting peaks
#IN_FN u (x_val(($1+$2)/2.0)):4 w lp pt 7 pointsize 0.3 lc rgb "blue" not

# boxxyerrorbars: x y xlow xhigh ylow yhigh
