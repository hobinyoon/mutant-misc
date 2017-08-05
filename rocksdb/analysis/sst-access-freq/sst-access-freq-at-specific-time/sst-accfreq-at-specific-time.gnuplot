# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
OUT_FN = system("echo $OUT_FN")
OUT_FN2 = system("echo $OUT_FN2")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

if (1) {
	set terminal unknown
	plot IN_FN u 0:4 w p
	X_MIN=GPVAL_DATA_X_MIN
	X_MAX=GPVAL_DATA_X_MAX
	Y_MIN=GPVAL_DATA_Y_MIN
	Y_MAX=GPVAL_DATA_Y_MAX
}

set terminal pdfcairo enhanced size 2.1in, (2.1*0.85)in
set output OUT_FN

set border front lc rgb "#808080" back
set grid xtics mxtics ytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0, 10
set mxtics 2
set ytics nomirror tc rgb "black" #autofreq 0,2*60*60
set tics back

set logscale y

# Order by Sst access freq
set ytics nomirror tc rgb "black" ( \
	"1" 1, \
	"10^{-1}" 0.1, \
	"10^{-2}" 0.01, \
	"10^{-3}" 0.001, \
	"10^{-4}" 0.0001 \
)
set yrange [0.0001:]
set ylabel "Access frequency" offset 0,-0.2
# Normalized Reads/sec
set xlabel "Access frequency rank"
#set xlabel "SSTables ordered by access frequencies"
#set xlabel "SSTable rank (ordered by their access frequencies)"
plot '< sort -rnk 4 ' . IN_FN u 0:($4/Y_MAX) w p pt 7 pointsize 0.3 not

set terminal pdfcairo enhanced size 2.0in, (2.0*0.85)in
set output OUT_FN2

set tmargin screen 0.96
set lmargin screen 0.26
set rmargin screen 0.95

set ylabel "Access frequency\n(reads / sec)" offset 1,0
# will be explained in detail in the later section

# By Age
set xlabel "Age (days)"
plot IN_FN u 6:4 w p pt 7 pointsize 0.3 not

# By SstID rank (age rank)
#set xlabel "Sst ID rank"
set xlabel "SSTable age rank"
#set xlabel "SSTable age rank\n(0 is the youngest)"
set ylabel "Access frequency" offset -0.5,0
set xtics nomirror tc rgb "black" autofreq 0,10
set ytics nomirror tc rgb "black" ( \
	"1" 1, \
	"10^{-1}" 0.1, \
	"10^{-2}" 0.01, \
	"10^{-3}" 0.001, \
	"10^{-4}" 0.0001 \
)
set xrange [:X_MAX]
set yrange [0.0001:]
plot IN_FN u (X_MAX-$0):($4/Y_MAX) w p pt 7 pointsize 0.3 not

# Order by level and SstID
set xlabel "SSTable ordered by level and ID"
#set palette model RGB defined ( 0 "red", 1 "#FF00FF", 2 "blue" )
#set palette model RGB defined ( 0 "red", 1 "green", 2 "blue" )
#set palette model RGB defined ( 0 "red", 1 "#8A2BE2", 2 "blue" )
set palette model RGB defined ( 0 "red", 1 "#D2691E", 2 "blue" )
unset colorbox
plot '< sort -nk 5 ' . IN_FN u 0:4:5 w p palette pt 7 pointsize 0.3 not

if (0) {
	# Legend
	set obj circle at graph 0.8,0.9 size graph 0.01 fs solid fc rgb "red"
	set obj circle at graph 0.8,0.8 size graph 0.01 fs solid fc rgb "#D2691E"
	set obj circle at graph 0.8,0.7 size graph 0.01 fs solid fc rgb "blue"

	plot '< sort -rnk 4 ' . IN_FN u 0:($4/Y_MAX):5 w p palette pt 7 pointsize 0.3 not
}

set xlabel "Access frequency rank"
set ylabel "Access frequency\n" offset 0,-0.2 tc rgb "white"
set key at graph 0.97,0.92 samplen 0.1

if (0) {
	# http://stackoverflow.com/questions/29622885/how-set-point-type-from-data-in-gnuplot
	set encoding utf8
	#symbol(z) = "•✷+△♠□♣♥♦"[int(z):int(z)]
	symbol(z) = "○△□"[int(z):int(z)]
	plot '< sort -rnk 4 ' . IN_FN \
		 u 0:($4/Y_MAX):(symbol($5 + 1)):5 with labels tc palette font ",8" not
}

# The depth ordering of points is not by the frequency rank.
if (1) {
	LW=2
	plot '< sort -rnk 4 ' . IN_FN \
		 u ($5 == 0 ? $0 : 1/0):($4/Y_MAX) w p pointsize 0.9 pt 4  lw LW lc rgb "red"     t "L0", \
	"" u ($5 == 1 ? $0 : 1/0):($4/Y_MAX) w p pointsize 0.9 pt 71 lw LW lc rgb "#D2691E" t "L1", \
	"" u ($5 == 2 ? $0 : 1/0):($4/Y_MAX) w p pointsize 0.9 pt 8  lw LW lc rgb "blue"    t "L2"
}
