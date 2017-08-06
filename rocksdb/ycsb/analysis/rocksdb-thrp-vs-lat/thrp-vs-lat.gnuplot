# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEY)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

if (1) {
  set noxtics
  set noytics
  set noborder
  f(x) = x
  set label 1 at screen 0.5, screen 0.5 \
    "1: read latency\n2: write latency" \
    center
  plot f(x) lc rgb "#F0F0F0" not
}

unset label 1

set xtics nomirror tc rgb "black" ( \
   "0"      0 \
,  "2"  20000 \
,  "4"  40000 \
,  "6"  60000 \
,  "8"  80000 \
, "10" 100000 \
, "12" 120000 \
, "14" 140000 \
)

#y_scale = "linear"
y_scale = "log"

if (y_scale eq "linear") {
	set ytics nomirror tc rgb "black" ( \
		 "0"     0 \
	,  "2"  2000 \
	,  "4"  4000 \
	,  "6"  6000 \
	,  "8"  8000 \
	, "10" 10000 \
	, "12" 12000 \
	, "14" 14000 \
	)
	set yrange [0:20000]
} else { if (y_scale eq "log") {
	set logscale y
	set ytics nomirror tc rgb "black" ( \
		"1"          1 \
	, "10"        10 \
	, "10^2"     100 \
	, "10^3"    1000 \
	, "10^4"   10000 \
	, "10^5"  100000 \
	, "10^6" 1000000 \
	)
	set yrange [1:]
} }

set grid xtics mxtics ytics back lc rgb "#808080"
set border (1+2+4+8) back lc rgb "#808080"

set xlabel "IOPS (10K IOs/sec)"
set ylabel "Latency (ms)" offset -0.5, 0

set xrange [0:10000]

#plot_type = "dot"
plot_type = "whisker"

# Read latency
if (1) {
	col_base = 3

	if (plot_type eq "dot") {
		plot \
		FN_IN u 2:(column(col_base + 0)) w lp pt 7 ps 0.4 lc rgb "blue" t "RocksDB on EBS Mag"
	} else { if (plot_type eq "whisker") {
		plot \
		FN_IN u 2:(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)) w candlesticks lw 2 lc rgb "blue" not, \
		FN_IN u 2:(column(col_base + 4)):(column(col_base + 3)):(column(col_base + 8)):(column(col_base + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \

		# Avg is not very useful
		#FN_IN u 2:(column(col_base + 0)) w p pt 7 ps 0.4 lc rgb "red" not

		# candlesticks
		# x  box_min  whisker_min  whisker_high  box_high
		# iops    5p           1p           99p       90p
		# 2        7            6            11         9
	} }
}

# Write latency
if (1) {
	col_base = 14

	if (plot_type eq "dot") {
		plot \
		FN_IN u 2:(column(col_base + 0)) w lp pt 7 ps 0.4 lc rgb "blue" t "RocksDB on EBS Mag"
	} else { if (plot_type eq "whisker") {
		plot \
		FN_IN u 2:(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)) w candlesticks lw 2 lc rgb "blue" not, \
		FN_IN u 2:(column(col_base + 4)):(column(col_base + 3)):(column(col_base + 8)):(column(col_base + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
	} }
}
