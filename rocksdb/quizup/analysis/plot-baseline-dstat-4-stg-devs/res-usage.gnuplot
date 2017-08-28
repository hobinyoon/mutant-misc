# Tested with gnuplot 4.6 patchlevel 4

FN_IN_LOCAL_SSD = system("echo $FN_IN_LOCAL_SSD")
FN_IN_EBS_GP2 = system("echo $FN_IN_EBS_GP2")
FN_IN_EBS_ST1 = system("echo $FN_IN_EBS_ST1")
FN_IN_EBS_SC1 = system("echo $FN_IN_EBS_SC1")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("FN_OUT=%s", FN_OUT)

set xdata time
# 0711-170251
set timefmt "%m%d-%H%M%S"
set format x "%d-%H"

# Manually setting the range. You don't need to get the data range.
if (0) {
	set terminal unknown
	plot FN_IN_LOCAL_SSD u 25:29 w l
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
}

set terminal pdfcairo enhanced size 6in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080" back
set grid xtics mxtics ytics mytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0,4*3600
set mxtics 4
set tics front

set xlabel "Time (day-hour)"

set xrange["0726-200000":"0727-110000"]

set samples 1000

PS=0.15
LW=4

COLORS="#0000FF #006400 #A52A2A #FF0000"
COLORS_LIGHT="#8080FF #80CB80 #E1B8B8 #FF8080"

set key horiz maxrows 1 width 0

if (1) {
	set title "CPU usage (user + sys)"
	set ylabel "CPU (%)"
	set yrange[0:1.5]
	set ytics nomirror tc rgb "black" format "%.1f" autofreq 0,0.5
	set nomytics
	plot \
	FN_IN_EBS_SC1   u 25:($29+$30) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:($29+$30) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:($29+$30) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:($29+$30) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:($29+$30) w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($29+$30) w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($29+$30) w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($29+$30) w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "IO wait time"
	set ylabel "CPU (%)"
	set yrange[0:4]
	set ytics nomirror tc rgb "black" format "%.1f" autofreq 0,1
	set mytics 2
	plot \
	FN_IN_EBS_SC1   u 25:31 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:31 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:31 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:31 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:31 w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:31 w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:31 w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:31 w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

# Nothing interesting here
if (0) {
	set title "Memory:buffer"
	set ylabel "MB"
	set yrange[0:300]
	set ytics nomirror tc rgb "black" autofreq 0,100 format "%.0f"
	#set mytics 2
	plot \
	FN_IN_LOCAL_SSD u 25:($17/1000.0) w l lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($17/1000.0) w l lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($17/1000.0) w l lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($17/1000.0) w l lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "Memory:used"
	set ylabel "GB"
	set yrange[1.0:1.8]
	set ytics nomirror tc rgb "black" autofreq 0,0.2 format "%.1f"
	set mytics 2
	plot \
	FN_IN_LOCAL_SSD u 25:($20/1000000.0) w l lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($20/1000000.0) w l lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($20/1000000.0) w l lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($20/1000000.0) w l lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "Memory:cache"
	set ylabel "GB"
	set yrange[2:8]
	set ytics nomirror tc rgb "black" autofreq 0,1 format "%.0f"
	set nomytics
	plot \
	FN_IN_LOCAL_SSD u 25:($18/1000000.0) w l lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($18/1000000.0) w l lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($18/1000000.0) w l lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($18/1000000.0) w l lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "DB data disk IO:read"
	set ylabel "IO/s"
	set yrange[0:200]
	set ytics nomirror tc rgb "black" autofreq 0,50 format "%.0f"
	set mytics 5
	plot \
	FN_IN_EBS_SC1   u 25:15 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:15 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:15 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:13 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:13 w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:15 w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:15 w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:15 w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "DB data disk IO:write"
	set ylabel "IO/s"
	set yrange[0:200]
	set ytics nomirror tc rgb "black" autofreq 0,50 format "%.0f"
	set mytics 5
	plot \
	FN_IN_EBS_SC1   u 25:16 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:16 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:16 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:14 w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:14 w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:16 w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:16 w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:16 w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

# MS/s is very similar across devices. Makes sense
if (1) {
	set title "DB data disk IO:read"
	set ylabel "MB/s"
	set yrange[0:1.8]
	set ytics nomirror tc rgb "black" autofreq 0,0.5 format "%.1f"
	set mytics 5
	plot \
	FN_IN_EBS_SC1   u 25:($7/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:($7/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:($7/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:($5/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:($5/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($7/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($7/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($7/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}

if (1) {
	set title "DB data disk IO:write"
	set ylabel "MB/s"
	set yrange[0:20]
	set ytics nomirror tc rgb "black" autofreq 0,5 format "%.0f"
	set mytics 5
	plot \
	FN_IN_EBS_SC1   u 25:($8/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 1) not, \
	FN_IN_EBS_ST1   u 25:($8/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 2) not, \
	FN_IN_EBS_GP2   u 25:($8/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 3) not, \
	FN_IN_LOCAL_SSD u 25:($6/1024.0/1024.0) w p pt 7 pointsize PS lc rgb word(COLORS_LIGHT, 4) not, \
	FN_IN_LOCAL_SSD u 25:($6/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 4) t "Local SSD"  , \
	FN_IN_EBS_GP2   u 25:($8/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 3) t "EBS SSD"    , \
	FN_IN_EBS_ST1   u 25:($8/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 2) t "EBS Mag"    , \
	FN_IN_EBS_SC1   u 25:($8/1024.0/1024.0) w l smooth bezier lw LW lc rgb word(COLORS, 1) t "EBS MagCold"
}
