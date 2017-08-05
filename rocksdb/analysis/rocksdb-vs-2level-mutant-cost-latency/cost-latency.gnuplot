#! /usr/bin/gnuplot

IN_FN_ROCKSDB = system("echo $IN_FN_ROCKSDB")
IN_FN_MUTANT = system("echo $IN_FN_MUTANT")
OUT_FN = system("echo $OUT_FN")
OUT_FN1 = system("echo $OUT_FN1")
OUT_FN2 = system("echo $OUT_FN2")
OUT_FN3 = system("echo $OUT_FN3")
OUT_FN4 = system("echo $OUT_FN4")

poster = 0

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

if (poster) {
	set terminal pdfcairo enhanced size 3in, (3*0.85)in
} else {
	set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
	set output OUT_FN
}

set xlabel "Storage cost (cent)"
set ylabel "Read latency (ms)" offset 1.0,0

set xtics nomirror tc rgb "black" autofreq 0,10 #format "%0.1f" #autofreq 0,0.1
set ytics nomirror tc rgb "black" autofreq 0,40
set grid xtics ytics back lw 3 lc rgb "#808080"
set border front lc rgb "#808080"

set xrange [0:]
set yrange [0:]

LW=4

# Legend
if (1) {
	x_c=0.78
	y_t=0.92
	y_b=y_t-0.20
	#LC="#404040"
	LC="#606060"
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

LW=4
PS=0.4

# RocksDB only
if (poster) {
	set output OUT_FN1
}
plot \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \


# RocksDB, Mutant
if (poster) {
	set output OUT_FN2
}

set label 10 "Mutant" at 16, 90 center tc rgb "#8A2BE2"

plot \
IN_FN_MUTANT u (strcol(1) eq "F" ? ($3*100) : 1/0):($7/1000):($8/1000):($9/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "F" ? ($3*100) : 1/0):($7/1000) \
	w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? ($2*100) : 1/0):($6/1000):("EBS Mag")    w labels left offset 1,0   tc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):("Local\nSSD") w labels      offset 0,2.5 tc rgb "red"  not, \

# RocksDB, Mutant w metadata caching on
if (poster) {
	set output OUT_FN3
}
plot \
IN_FN_MUTANT u (strcol(1) eq "T" ? ($3*100) : 1/0):($7/1000):($8/1000):($9/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "T" ? ($3*100) : 1/0):($7/1000) \
	w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? ($2*100) : 1/0):($6/1000):("EBS Mag")    w labels left offset 1,0   tc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):("Local\nSSD") w labels      offset 0,2.5 tc rgb "red"  not, \

# RocksDB, Mutant wo/ metadata caching, Mutant
if (poster) {
	set output OUT_FN4
}
plot \
IN_FN_MUTANT u (strcol(1) eq "F" ? ($3*100) : 1/0):($7/1000):($8/1000):($9/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "F" ? ($3*100) : 1/0):($7/1000) \
	w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "T" ? ($3*100) : 1/0):($7/1000):($8/1000):($9/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "#8A2BE2" not, \
IN_FN_MUTANT u (strcol(1) eq "T" ? ($3*100) : 1/0):($7/1000) \
	w l lt 0 lw 5 lc rgb "#8A2BE2" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):($7/1000):($8/1000) \
	w yerrorbars pt 7 pointsize PS lw LW lc rgb "red" not, \
IN_FN_ROCKSDB u (strcol(1) eq "ebs-st1"    ? ($2*100) : 1/0):($6/1000):("EBS Mag")    w labels left offset 1,0   tc rgb "blue" not, \
IN_FN_ROCKSDB u (strcol(1) eq "local-ssd1" ? ($2*100) : 1/0):($6/1000):("Local\nSSD") w labels      offset 0,2.5 tc rgb "red"  not, \
