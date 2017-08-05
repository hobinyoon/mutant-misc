# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
IN_FN_BASELINE = "data-unmodified-rocksdb-latency-by-dev-by-memsize"
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)


#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set terminal pdfcairo enhanced size 3in, 2.5in
set output OUT_FN

set border front lc rgb "#E0E0E0" back
set xtics nomirror tc rgb "black" ( \
"2^{-6}" 2**(-6), \
"2^{-4}" 2**(-4), \
"2^{-2}" 2**(-2), \
1, \
"2^{2}" 2**(2), \
"2^{4}" 2**(4), \
"2^{6}" 2**(6), \
"2^{8}" 2**(8) \
)
set ytics nomirror tc rgb "black" #format "%.1f"

set grid xtics ytics back lc rgb "#808080"

data_size=2367.679

color_mutant="#a020f0"
color_fast="red"
color_slow="blue"

set xlabel "Mutant with different SSTable\nmigration temperature threshold" tc rgb color_mutant
set ylabel "Read latency (sec)" offset 2,0

x_val(a)=a / 1024.0
y_val(a)=a / 1000.0

set logscale x
set logscale y

set xrange [2**(-7) / 1.8 : 2**9 * 1.8]

# With sst_mig_temp_threshold 2^(-6), all SSTables stay in the fast storage.

LW=6

# Legend
if (0) {
	c0="#404040"
	#set size 0.98,1
	x0=0.75
	y0=0.3
	y1=0.5
	y2=0.6
	y3=0.7
	set arrow from graph x0, graph y0 to graph x0, graph y3 nohead lw LW lc rgb c0
	set obj circle at graph x0, graph y0 size graph 0.013 fc rgb c0 fs solid

	x_width=0.01
	set arrow from graph x0-x_width, graph y1 to graph x0+x_width, graph y1 nohead lw LW lc rgb c0
	set arrow from graph x0-x_width, graph y2 to graph x0+x_width, graph y2 nohead lw LW lc rgb c0
	set arrow from graph x0-x_width, graph y3 to graph x0+x_width, graph y3 nohead lw LW lc rgb c0

	set label "avg" at graph x0, graph y0 offset 1.0
	set label "99th" at graph x0, graph y1 offset 1.0
	set label "99.9th" at graph x0, graph y2 offset 1.0
	set label "99.99th" at graph x0, graph y3 offset 1.0

	# Tried to make a white background behind the legend. Didn't like it.
	#set style rect fc lt -1 fs solid 0.15 noborder
	#set style line 1 lt rgb "white"
	#set obj rect from 258,0.01 to 2**14,100000 fc ls 1 fs solid #bo -1
}


stg_devs = "ebs-gp2 ebs-st1 ebs-sc1"

do for [i=1:words(stg_devs)] {
	stg_dev = word(stg_devs, i)

	slow_dev_label = "
	if (stg_dev eq "ebs-gp2") {
		slow_dev_label="EBS SSD"
	} else { if (stg_dev eq "ebs-st1") {
		slow_dev_label="EBS Magnetic"
	} else { if (stg_dev eq "ebs-sc1") {
		slow_dev_label="EBS Magnetic Cold"
	} } }

	key_rocksdb_fast_stg = "Unmodified RocksDB: Local SSD"
	key_mutant = sprintf("Mutant: Local SSD + %s", slow_dev_label)
	key_rocksdb_slow_stg = sprintf("Unmodified RocksDB: %s", slow_dev_label)
	if (stg_dev eq "ebs-gp2") {
		Y_MAX=10
	} else { if (stg_dev eq "ebs-st1") {
		Y_MAX=1000
	} else { if (stg_dev eq "ebs-sc1") {
		Y_MAX=1000
	} } }

	PS=0.7
	WING_LENGTH=1.1

	if (1) {
		set size 0.93,0.85
		set nokey
		set label 1 "Unmodified\nRocksDB on\nLocal SSD" at 0.125, screen 0.97 center tc rgb color_fast
		set label 3 sprintf("Unmodified\nRocksDB on\n%s", slow_dev_label) at 512, screen 0.97 center tc rgb color_slow
	} else {
		set key above
	}

	x_fast_stg=2**(-7)
	x_slow_stg=2**9

	base=15
	plot \
	IN_FN_BASELINE u (strcol(1) eq "local-ssd1" && strcol(2) eq "2048" ? x_fast_stg/WING_LENGTH : 1/0):(y_val(column(base+9))):(x_fast_stg*WING_LENGTH - x_fast_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_fast t key_rocksdb_fast_stg, \
	IN_FN_BASELINE u (strcol(1) eq "local-ssd1" && strcol(2) eq "2048" ? x_fast_stg/WING_LENGTH : 1/0):(y_val(column(base+6))):(x_fast_stg*WING_LENGTH - x_fast_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_fast not, \
	IN_FN_BASELINE u (strcol(1) eq "local-ssd1" && strcol(2) eq "2048" ? x_fast_stg/WING_LENGTH : 1/0):(y_val(column(base+3))):(x_fast_stg*WING_LENGTH - x_fast_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_fast not, \
	IN_FN_BASELINE u (strcol(1) eq "local-ssd1" && strcol(2) eq "2048" ? x_fast_stg : 1/0):(y_val(column(base+0))) w p pt 7 pointsize PS lc rgb color_fast not, \
	IN_FN_BASELINE u (strcol(1) eq "local-ssd1" && strcol(2) eq "2048" ? x_fast_stg : 1/0):(y_val(column(base+0))):(0):(y_val(column(base+9)) - y_val(column(base+ 0))) w vectors nohead lw LW lc rgb color_fast not, \
	\
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+9))) w l lw LW lt 0 lc rgb color_mutant not, \
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+6))) w l lw LW lt 0 lc rgb color_mutant not, \
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+3))) w l lw LW lt 0 lc rgb color_mutant not, \
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+0))) w l lw LW lt 0 lc rgb color_mutant not, \
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+0))) w p pt 7 pointsize PS lc rgb color_mutant not, \
	\
	IN_FN u (strcol(1) eq stg_dev ? $2/WING_LENGTH : 1/0):(y_val(column(base+9))):($2*WING_LENGTH - $2/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_mutant t key_mutant, \
	IN_FN u (strcol(1) eq stg_dev ? $2/WING_LENGTH : 1/0):(y_val(column(base+6))):($2*WING_LENGTH - $2/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_mutant not, \
	IN_FN u (strcol(1) eq stg_dev ? $2/WING_LENGTH : 1/0):(y_val(column(base+3))):($2*WING_LENGTH - $2/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_mutant not, \
	\
	IN_FN u (strcol(1) eq stg_dev ? $2 : 1/0):(y_val(column(base+ 0))):(0):(y_val(column(base+9)) - y_val(column(base+ 0))) w vectors nohead lw LW lc rgb color_mutant not, \
	\
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg/WING_LENGTH : 1/0):(y_val(column(base+9))):(x_slow_stg*WING_LENGTH - x_slow_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_slow t key_rocksdb_slow_stg, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg/WING_LENGTH : 1/0):(y_val(column(base+6))):(x_slow_stg*WING_LENGTH - x_slow_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_slow not, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg/WING_LENGTH : 1/0):(y_val(column(base+3))):(x_slow_stg*WING_LENGTH - x_slow_stg/WING_LENGTH):(0) w vectors nohead lw LW lc rgb color_slow not, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg : 1/0):(y_val(column(base+0))) w p pt 7 pointsize PS lc rgb color_slow not, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg : 1/0):(y_val(column(base+0))):(0):(y_val(column(base+9)) - y_val(column(base+ 0))) w vectors nohead lw LW lc rgb color_slow not, \
	\
	IN_FN_BASELINE u (strcol(1) eq stg_dev && stg_dev eq "ebs-gp2" && strcol(2) eq "2048" ? x_slow_stg : (2**100)):(y_val(column(base+9))):("99.99th") w labels offset 1.0,0 left, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && stg_dev eq "ebs-st1" && strcol(2) eq "2048" ? x_slow_stg : (2**100)):(y_val(column(base+9))):("99.99th") w labels offset 1.0,0 left, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && stg_dev eq "ebs-sc1" && strcol(2) eq "2048" ? x_slow_stg : (2**100)):(y_val(column(base+9))):("99.99th") w labels offset 1.0,0.5 left, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg : 1/0):(y_val(column(base+6))):("99.9th")  w labels offset 1.0,0 left, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg : 1/0):(y_val(column(base+3))):("99th")    w labels offset 1.0,0 left, \
	IN_FN_BASELINE u (strcol(1) eq stg_dev && strcol(2) eq "2048" ? x_slow_stg : 1/0):(y_val(column(base+0))):("avg")     w labels offset 1.0,0 left

	# Use 2**100 instead of 1/0 to avoid "warning: Skipping data file with no valid points"
	#IN_FN_BASELINE u (strcol(1) eq stg_dev && stg_dev eq "ebs-gp2" && strcol(2) eq "2048" ? x_slow_stg : (2**100)):(y_val(column(base+9))):("99.99th") w labels offset 1.0,0 left
}
