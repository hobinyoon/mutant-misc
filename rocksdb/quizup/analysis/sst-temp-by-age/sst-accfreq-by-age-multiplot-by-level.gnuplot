# Tested with gnuplot 4.6 patchlevel 4

IN_DN = system("echo $IN_DN")
SST_IDS = system("echo $SST_IDS")
SST_SIZES = system("echo $SST_SIZES")
LEVEL = system("echo $LEVEL") + 0
AGE_DELETED = system("echo $AGE_DELETED")
AGE_DELETED_MAX = system("echo $AGE_DELETED_MAX") + 0
ACCFREQ_MAX_ALL_SST_IN_LEVEL = system("echo $ACCFREQ_MAX_ALL_SST_IN_LEVEL") + 0
TEMP_MAX_ALL_SST_IN_LEVEL = system("echo $TEMP_MAX_ALL_SST_IN_LEVEL") + 0
ACCFREQ_MAX = system("echo $ACCFREQ_MAX")
TEMP_MAX = system("echo $TEMP_MAX")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set border front lc rgb "#808080" back
set grid xtics x2tics ytics back lc rgb "#808080"

if (LEVEL == 0) {
	# x values in hours
	set xtics nomirror tc rgb "black" format "%.0fh" autofreq 0,1
	x_val(x)=x/3600.0
} else {
if (LEVEL == 1) {
	# x values in days
	set xtics nomirror tc rgb "black" format "%.0fd" autofreq 0,1
	x_val(x)=x/24.0/3600.0
} else {
if (LEVEL == 2) {
	# x values in days
	set xtics nomirror tc rgb "black" format "%.0fd" autofreq 0,1
	x_val(x)=x/24.0/3600.0
} } }

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

set ytics  nomirror tc rgb "black"
#set y2tics nomirror tc rgb "blue"
set tics back

set xlabel "SSTables age"
#set ylabel "Access freq calculated every minute\n(cnt / 64MB / sec)"

#set logscale y
#set yrange[0:ACCFREQ_MAX_ALL_SST_IN_LEVEL]
set xrange[0:x_val(AGE_DELETED_MAX)]

set style fill transparent solid 0.1 border

# Dummy objects
#set arrow 1 from 0,0 to 1,1

do for [i=1:words(SST_IDS)] {
	# Tried to get Y_MAX, but didn't work. It prevents generating multi-plot pdfs.
	if (0) {
		set terminal unknown
		plot IN_DN . "/" . word(SST_IDS, i) u 0:7 w p
		Y_MAX=GPVAL_DATA_Y_MAX
		print sprintf("Y_MAX=%d", Y_MAX)
	}

	#set yrange[0:(word(ACCFREQ_MAX, i) + 0.0)]
	##set y2range[0:(word(TEMP_MAX, i) + 0.0)]
	#set y2range[0:(word(ACCFREQ_MAX, i) + 0.0)]
	y_max = word(ACCFREQ_MAX, i) * 1.1
	set yrange[0:y_max]
	set y2range[0:y_max]

	set title (sprintf("sst id %s, level %d, size %.2f MB", word(SST_IDS, i), LEVEL, word(SST_SIZES, i)/1024.0/1024.0)) offset 0,-1
	set x2tics nomirror tc rgb "black" ( "deleted" x_val(word(AGE_DELETED, i)) )

	#unset arrow 1
	#y1=ACCFREQ_MAX_ALL_SST_IN_LEVEL
	#set arrow 1 from (x_val(word(AGE_DELETED, i) + 0.0)), 0 to (x_val(word(AGE_DELETED, i) + 0.0)), y1 nohead lt 0 lc rgb "black" lw 5

	plot \
	IN_DN . "/" . word(SST_IDS, i) u (x_val($4)):7    w l                lc rgb "red"  not, \
	""                             u (x_val($4)):8    w l axes x1y2 lw 4 lc rgb "blue" not, \
	""                             u (x_val($4)):(-1) w l           lw 6 lc rgb "red"  t "Access freq (cnt / 64MB / sec)", \
	""                             u (x_val($4)):(-1) w l axes x1y2 lw 6 lc rgb "blue" t "Temperature"

	#IN_DN . "/" . word(SST_IDS, i) u (x_val($4)):(0):(x_val($4)):(x_val($5)):(0):7 w boxxyerrorbar lc rgb "red"  not, \

}

# The linepoint connecting peaks
#IN_FN u (x_val(($1+$2)/2.0)):4 w lp pt 7 pointsize 0.3 lc rgb "blue" not

# boxxyerrorbars: x y xlow xhigh ylow yhigh
