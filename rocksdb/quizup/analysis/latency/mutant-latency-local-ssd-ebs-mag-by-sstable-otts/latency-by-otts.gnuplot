#! /usr/bin/gnuplot

IN_FN_ROCKSDB = system("echo $IN_FN_ROCKSDB")
IN_FN_MUTANT = system("echo $IN_FN_MUTANT")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 2.5in, (2.3*0.85)in
set output OUT_FN

set border (2) front lc rgb "#808080" back
set grid xtics back lc rgb "#808080"
set xtics out nomirror tc rgb "black" ( \
  "2^{-8}" 2**(-8), \
  "2^{-4}" 2**(-4), \
  "2^{ 0}" 2**( 0), \
  "2^{ 4}" 2**( 4), \
  "2^{ 8}" 2**( 8) \
	)
set ytics nomirror tc rgb "black"
set tics back

set xlabel "SSTable OTT" offset -2.5,0
set ylabel "Read latency (ms)" offset 1,0

set logscale x

X_MIN=(2**(-9)) / 1.5
X_MAX=(2**17) * 1.5

set xrange[X_MIN:X_MAX]
set yrange[0:]

LW=4
PS=0.4

RDB_X=2**14
M_X_MAX=2**12

Y_MAX=250

# Finish the rest of the border lines
set arrow 1 from X_MIN,0     to M_X_MAX,0     nohead
set arrow 2 from X_MIN,Y_MAX to M_X_MAX,Y_MAX nohead
set arrow 3 from M_X_MAX,0   to M_X_MAX,Y_MAX nohead

# Finish the grid
do for [i=1:4] {
	set arrow (10+i) from X_MIN,(i*50) to M_X_MAX,(i*50) nohead lt 0
}

LW1=7

plot \
IN_FN_MUTANT u (strcol(1) eq "F" ? $2 : 1/0):($7/1000):($8/1000):($9/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "F" ? $2 : 1/0):($7/1000) \
	w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? RDB_X : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? RDB_X : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? RDB_X*4 : 1/0):($6/1000 + 15):("RocksDB\n(EBS Mag)") w labels rotate by 90 not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? RDB_X*4 : 1/0):($6/1000 - 15):("RocksDB\n(Local SSD)") w labels rotate by 90 not, \
IN_FN_ROCKSDB u (X_MIN):(strcol(1) eq "ebs-st1"    ? $6/1000 : 1/0):(M_X_MAX*1.5):(0) w vectors nohead lt 0 lw LW1 not, \
IN_FN_ROCKSDB u (X_MIN):(strcol(1) eq "local-ssd1" ? $6/1000 : 1/0):(M_X_MAX*1.5):(0) w vectors nohead lt 0 lw LW1 not, \

# Write latency plot
if (1) {

	# Legend
	if (1) {
		x_c=0.1
		y_t=0.92
		y_b=y_t-0.275
		LC="#505050"
		#LC="black"
		set arrow from graph x_c, y_b to graph x_c, y_t nohead lw LW lc rgb LC
		x_l=x_c-0.008
		x_r=x_c+0.008
		set arrow from graph x_l, y_t to graph x_r, y_t nohead lw LW lc rgb LC
		set arrow from graph x_l, y_b to graph x_r, y_b nohead lw LW lc rgb LC
		y3=(y_t+y_b)/2
		set object circle at graph x_c, y3 size screen 0.011 fs solid noborder fc rgb LC
		set label "99%" at graph x_c, y_t offset 0.9,0
		set label "Avg" at graph x_c, y3 offset 0.9,0
		set label "1%"  at graph x_c, y_b offset 0.9,0
	}

	set ylabel "Write latency (ms)" offset 1,0

	Y_MAX=75
	set yrange[0:Y_MAX]

	# Finish the rest of the border lines
	set arrow 2 from X_MIN,Y_MAX to M_X_MAX,Y_MAX nohead
	set arrow 3 from M_X_MAX,0   to M_X_MAX,Y_MAX nohead

	# Finish the grid
	do for [i=1:7] {
		set arrow (10+i) from X_MIN,(i*10) to M_X_MAX,(i*10) nohead lt 0
	}

	plot \
	IN_FN_MUTANT u (strcol(1) eq "F" ? $2 : 1/0):($4/1000):($5/1000):($6/1000) \
		w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
	IN_FN_MUTANT u (strcol(1) eq "F" ? $2 : 1/0):($4/1000) \
		w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
	IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? RDB_X   : 1/0):($3/1000):($4/1000):($5/1000) \
		w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
	IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? RDB_X*2 : 1/0):($3/1000):($4/1000):($5/1000) \
		w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \
	IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? RDB_X*3 : 1/0):($3/1000 + 25):("RocksDB\n(EBS Mag)") w labels rotate by 90 not, \
	IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? RDB_X*8 : 1/0):($3/1000 - 10):("RocksDB\n(Local SSD)") w labels rotate by 90 not, \
	IN_FN_ROCKSDB u (X_MIN):(strcol(1) eq "ebs-st1"    ? $3/1000 : 1/0):(M_X_MAX*1.5):(0) w vectors nohead lt 0 lw LW1 not, \
	IN_FN_ROCKSDB u (X_MIN):(strcol(1) eq "local-ssd1" ? $3/1000 : 1/0):(M_X_MAX*1.5):(0) w vectors nohead lt 0 lw LW1 not
}
