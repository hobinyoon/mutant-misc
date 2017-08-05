# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
IN_FN_INDIVIDUAL = system("echo $IN_FN_INDIVIDUAL")
OUT_FN = system("echo $OUT_FN")

set print "-"
#print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 3.0in, (3.0*0.85)in
set output OUT_FN

set bmargin at screen 0.2

set ylabel "Read latency (ms)" offset 1.5,0

set xtics nomirror scale 0,0 tc rgb "black" ( \
"Local\nSSD" 1, \
"EBS\nSSD" 2, \
"EBS\nMag" 3, \
"EBS\nMag Cold" 4 \
)
set ytics nomirror tc rgb "black"
set decimal locale
set format y "%'g"
set grid xtics ytics back lc rgb "#808080"
set border front lc rgb "#808080"

set xrange [0.3:5.0]

# Keep ms
y_val(a)=a

color_unmodified="red"
color_metadata_caching="black"

colors_metadata_cached="red blue"

bar_width=0.30
bar_spacing=0.10

stg_devs="local-ssd1 ebs-gp2 ebs-st1 ebs-sc1"

metadata_cached_str="F T"

x_avg_l(stg_idx, metadata_cached)=(strcol(1) eq word(stg_devs, stg_idx) \
														&& strcol(2) eq word(metadata_cached_str, metadata_cached + 1) \
														? stg_idx + (metadata_cached-0.5)*2 * (bar_spacing/2.0+bar_width) : 1/0)

x_avg_r(stg_idx, metadata_cached)=(strcol(1) eq word(stg_devs, stg_idx) \
														&& strcol(2) eq word(metadata_cached_str, metadata_cached + 1) \
														? stg_idx + (metadata_cached-0.5)*2 * (bar_spacing/2.0) : 1/0)

x_avg_c(stg_idx, metadata_cached)=(strcol(1) eq word(stg_devs, stg_idx) \
														&& strcol(2) eq word(metadata_cached_str, metadata_cached + 1) \
														? stg_idx + (metadata_cached-0.5)*2 * (bar_spacing/2.0+bar_width/2.0) : 1/0)

if (0) {
	Y_MIN=70
	set yrange [Y_MIN:90]
} else {
	Y_MIN=10
	set yrange [Y_MIN:]
	set logscale y
}

LW=4

# Legend
if (1) {
	x_width=0.7
	y_height_ratio=1.8

	x0=0.5
	x1=x0+x_width
	y0=4000
	y1=y0*y_height_ratio
	set obj 1 rect from x0,y0 to x1,y1 fc rgb word(colors_metadata_cached, 1) fs solid 0.2 noborder
	set label 1 "Unmodified\nRocksDB" at x1,(y0+y1)/2 offset 1,0.5 tc rgb word(colors_metadata_cached, 1)

	y0=1200
	y1=y0*y_height_ratio
	set obj 2 rect from x0,y0 to x1,y1 fc rgb word(colors_metadata_cached, 2) fs solid 0.2 noborder
	set label 2 "With aggressive\nmetadata caching" at x1,(y0+y1)/2 offset 1,0.5 tc rgb word(colors_metadata_cached, 2)
	# Cache indices and bloom filters of level 1 or higher SSTables
}

# For Gets (reads)
if (1) {
	base=15

	plot \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+0)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) fs solid 0.2 noborder not, \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_c(stg_idx,metadata_cached)):(column(base+0)):(column(base+1)):(column(base+2)) \
				w yerrorbars pt 1 pointsize 0.00001 lc rgb word(colors_metadata_cached, metadata_cached + 1) lw LW not, \
	IN_FN u (x_avg_c(4,1)):(column(base+0)):("avg") w labels tc rgb "black" left offset 1,0 not, \
	IN_FN u (x_avg_c(4,1)):(column(base+1)):("min") w labels tc rgb "black" left offset 1,0 not, \
	IN_FN u (x_avg_c(4,1)):(column(base+2)):("max") w labels tc rgb "black" left offset 1,0 not
}

# yerrorbars: x y ylow yhigh

# Individual read latency plot
if (1) {
	# Unset legend
	unset obj 1
	unset label 1
	unset obj 2
	unset label 2

	PT=7
	PS=0.3

	#set title "Individual read latency"
	plot \
		for [stg_idx=1:4] \
			IN_FN_INDIVIDUAL u (strcol(2) eq word(stg_devs, stg_idx) && strcol(3) eq "F" ? stg_idx-0.1 : 1/0):25 \
				w p pt PT pointsize PS lc rgb "red" not, \
		for [stg_idx=1:4] \
			IN_FN_INDIVIDUAL u (strcol(2) eq word(stg_devs, stg_idx) && strcol(3) eq "T" ? stg_idx+0.1 : 1/0):25 \
				w p pt PT pointsize PS lc rgb "blue" not
}

# Write latency
if (1) {
	set notitle
	set ylabel "Write latency (ms)" offset 1.5,0

	# Legend
	if (1) {
		x_width=0.7
		y_height_ratio=1.8

		x0=0.5
		x1=x0+x_width
		y0=4000
		y1=y0*y_height_ratio
		set obj 1 rect from x0,y0 to x1,y1 fc rgb word(colors_metadata_cached, 1) fs solid 0.2 noborder
		set label 1 "Unmodified\nRocksDB" at x1,(y0+y1)/2 offset 1,0.5 tc rgb word(colors_metadata_cached, 1)

		y0=1200
		y1=y0*y_height_ratio
		set obj 2 rect from x0,y0 to x1,y1 fc rgb word(colors_metadata_cached, 2) fs solid 0.2 noborder
		set label 2 "With aggressive\nmetadata caching" at x1,(y0+y1)/2 offset 1,0.5 tc rgb word(colors_metadata_cached, 2)
		# Cache indices and bloom filters of level 1 or higher SSTables
	}

	base=3

	plot \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+0)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) fs solid 0.2 noborder not, \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_c(stg_idx,metadata_cached)):(column(base+0)):(column(base+1)):(column(base+2)) \
				w yerrorbars pt 1 pointsize 0.00001 lc rgb word(colors_metadata_cached, metadata_cached + 1) lw LW not, \
	IN_FN u (x_avg_c(4,1)):(column(base+0)):("avg") w labels tc rgb "black" left offset 1,0 not, \
	IN_FN u (x_avg_c(4,1)):(column(base+1)):("min") w labels tc rgb "black" left offset 1,0 not, \
	IN_FN u (x_avg_c(4,1)):(column(base+2)):("max") w labels tc rgb "black" left offset 1,0 not
}

# Individual write latency plot
if (1) {
	# Unset legend
	unset obj 1
	unset label 1
	unset obj 2
	unset label 2

	PT=7
	PS=0.3

	#set title "Individual write latency"
	plot \
		for [stg_idx=1:4] \
			IN_FN_INDIVIDUAL u (strcol(2) eq word(stg_devs, stg_idx) && strcol(3) eq "F" ? stg_idx-0.1 : 1/0):5 \
				w p pt PT pointsize PS lc rgb "red" not, \
		for [stg_idx=1:4] \
			IN_FN_INDIVIDUAL u (strcol(2) eq word(stg_devs, stg_idx) && strcol(3) eq "T" ? stg_idx+0.1 : 1/0):5 \
				w p pt PT pointsize PS lc rgb "blue" not
}

# Plot avg, 99th, 99.9th, and 99.00th. Didn't like it.
if (0) {
	set logscale y
	Y_MIN=10
	set yrange [Y_MIN:]
	plot \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+0)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) not, \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+3)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) not, \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+6)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) not, \
	for [stg_idx=1:4] \
		for [metadata_cached=0:1] \
			IN_FN u (x_avg_l(stg_idx,metadata_cached)):(Y_MIN):(x_avg_l(stg_idx,metadata_cached)):(x_avg_r(stg_idx,metadata_cached)) \
				:(Y_MIN):(column(base+9)) w boxxyerrorbars lc rgb word(colors_metadata_cached, metadata_cached + 1) not
}
# boxxyerrorbars: x y xlow xhigh ylow yhigh
