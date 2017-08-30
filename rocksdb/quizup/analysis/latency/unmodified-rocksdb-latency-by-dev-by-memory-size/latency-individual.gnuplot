# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)


#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set terminal pdfcairo enhanced size 3in, 2.5in
set output OUT_FN

set border front lc rgb "#808080" back
set xtics nomirror tc rgb "black" format "%.1f"
set ytics nomirror tc rgb "black" #format "%.1f"
#set tics front
set grid xtics ytics back lc rgb "#808080"

# What's the total data size? Sum of all SSTable sizes at the end of the
# simulation: 2367.679 MB. From
# ~/work/mutant/misc/rocksdb/analysis/storage/.result/170122-025119.060/data-size-by-stg-devs-by-time

data_size=2367.679

# Not very intuitive
#x_axis="data-to-mem-ratio"

x_axis="memory-size"

if (x_axis eq "data-to-mem-ratio") {
	set xlabel "Data size / memory size"
} else { if (x_axis eq "memory-size") {
	set xlabel "Memory size (GB)"
} }

set ylabel "Read latency (sec)" offset 2,0

LW=3

if (x_axis eq "data-to-mem-ratio") {
	set key top left
	# data size to memory size ratio
	x_val(a)=data_size / a
	set xrange [0.5:2.0]
} else { if (x_axis eq "memory-size") {
	set key top right
	x_val(a)=a / 1024.0
	y_val(a)=a / 1000.0
	#set xrange [1.1:4.3]
	set xrange [1.1:3.1]
} }

stg_devs = "local-ssd1 ebs-gp2 ebs-st1 ebs-sc1"

do for [i=1:words(stg_devs)] {
	stg_dev = word(stg_devs, i)

	if (stg_dev eq "local-ssd1") {
		set title "Local SSD" offset 0,0.5
		Y_MAX=100
	} else { if (stg_dev eq "ebs-gp2") {
		set title "EBS SSD"
		Y_MAX=100
	} else { if (stg_dev eq "ebs-st1") {
		set title "EBS Magnetic"
		Y_MAX=10000
	} else { if (stg_dev eq "ebs-sc1") {
		set title "EBS Magnetic Cold" offset 0,1.0
		Y_MAX=10000
	} } } }

	set yrange [0.01:Y_MAX]

	# Linear scale doesn't show much.
	set logscale y

	# Say that leftmost ones of st1 and sc1 couldn't keep up with the IO request
	# rates, which is not depicted in the chart
	# - Those are what makes the entire experiment slow down! Revisit! (st1, 1434
	#   or lower) (sc1, 1843 or lower)
	#
	# TODO: Plot the number of disk accesses. Amount reads. This will give you a
	# good idea of what's going on behind the scene. 20 mins.
	#
	# What's the goal of this experiment? What did you want to learn/show?
	# - What is the proper memory size for the experiment?
	#   - 3GB was too much to get meaningful result. 2GB would be nice.

	if (x_axis eq "memory-size") {
		# arrow and label IDs help overwrite the previous lines
		set arrow 1 from x_val(data_size), 0.01 to x_val(data_size), Y_MAX nohead lt 0 lw 6 lc rgb "blue" back
		set label 1 "Total SSTable size" at x_val(data_size), Y_MAX tc rgb "blue" center offset 0,0.7
	}

	# Do not plot with overloaded system experiments with (strcol(4) eq "F")
	#
	# 99.99th percentile doesn't look too distracting in the logscale plot.
	# Looked so in linear scale.

	base=25
	plot \
	IN_FN u ((strcol(2) eq stg_dev) && (strcol(4) eq "F") ? x_val($3) : 1/0):(y_val(column(base+19))) w p lw LW t "99.99th", \
	IN_FN u ((strcol(2) eq stg_dev) && (strcol(4) eq "F") ? x_val($3) : 1/0):(y_val(column(base+10))) w p lw LW t "99.9th", \
	IN_FN u ((strcol(2) eq stg_dev) && (strcol(4) eq "F") ? x_val($3) : 1/0):(y_val(column(base+ 1))) w p lw LW t "99th", \
	IN_FN u ((strcol(2) eq stg_dev) && (strcol(4) eq "F") ? x_val($3) : 1/0):(y_val(column(base+ 0))) w p lw LW t "avg", \

}
