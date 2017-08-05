# Tested with gnuplot 4.6 patchlevel 4

STG_CONF_LABEL = system("echo $STG_CONF_LABEL")
SST_MIG_TEMP_TH = system("echo $SST_MIG_TEMP_TH")
SIMULATION_TIME_BEGIN = system("echo $SIMULATION_TIME_BEGIN")
IN_FNS = system("echo $IN_FNS")

FN_IN_LOCAL_SSD = system("echo $FN_IN_LOCAL_SSD")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("IN_FNS=%s %d", IN_FNS, words(IN_FNS))
#print sprintf("OUT_FN=%s", OUT_FN)

set xdata time
# 0711-170251
set timefmt "%m%d-%H%M%S"
set format x "%d-%H"

# Set x range
if (1) {
	# Automatically using the first input data
	set terminal unknown
	plot word(IN_FNS, 1) u 25:13 w p
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
} else {
	# Manually: when you want to zoom into a specific region
	X_MIN="0726-200000"
	X_MAX="0727-110000"
}

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output OUT_FN

set border front lc rgb "#808080" back
set xtics nomirror tc rgb "black" autofreq 0,4*3600
#set nomxtics
#set tics front
set grid xtics ytics back lc rgb "#808080"

set xlabel "Time (day-hour)"

set xrange[X_MIN:X_MAX]

set samples 1000

PS=0.15
LW=4

COLORS="#0000FF #006400 #A52A2A #FF0000"
COLORS_LIGHT="#8080FF #80CB80 #E1B8B8 #FF8080"

set key top left horiz maxrows 1 width -1

set ylabel "IO/s"
# Manually set y max and ytics. There are big outliers like up to 4500
set yrange[0:200]
set ytics nomirror tc rgb "black" format "%.0f" autofreq 0,50

do for [i=1:words(IN_FNS)] {
	set title sprintf("Mutant stg conf: %s, Sst migration temperature threshold: %d", STG_CONF_LABEL, word(SST_MIG_TEMP_TH, i)+0)
	
	if (0) {
		# Include individual latency dots. Too much.
		plot \
		word(IN_FNS, i) u 25:13 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
		word(IN_FNS, i) u 25:14 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
		word(IN_FNS, i) u 25:15 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
		word(IN_FNS, i) u 25:16 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
		word(IN_FNS, i) u 25:13 w l smooth bezier lw LW lc rgb word(COLORS, 4) t "fast-dev:r", \
		word(IN_FNS, i) u 25:14 w l smooth bezier lw LW lc rgb word(COLORS, 3) t "fast-dev:w", \
		word(IN_FNS, i) u 25:15 w l smooth bezier lw LW lc rgb word(COLORS, 2) t "slow-dev:r", \
		word(IN_FNS, i) u 25:16 w l smooth bezier lw LW lc rgb word(COLORS, 1) t "slow-dev:w"
	} else {
		plot \
		word(IN_FNS, i) u 25:13 w l smooth bezier lw LW lc rgb word(COLORS, 4) t "fast-dev:r", \
		word(IN_FNS, i) u 25:14 w l smooth bezier lw LW lc rgb word(COLORS, 3) t "fast-dev:w", \
		word(IN_FNS, i) u 25:15 w l smooth bezier lw LW lc rgb word(COLORS, 2) t "slow-dev:r", \
		word(IN_FNS, i) u 25:16 w l smooth bezier lw LW lc rgb word(COLORS, 1) t "slow-dev:w"
	}
}
