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
  set label 1 at screen 0.025, screen 0.90 \
    "1: read latency" \
    . "\n2: read latency (1p, 5p, 50p, 90p, 99p)" \
    . "\n3: write latency" \
    left
  plot f(x) lc rgb "#F0F0F0" not
  unset label 1
}

set grid xtics mxtics ytics back lc rgb "#808080"
set border (1+2+4+8) back lc rgb "#808080"

set xlabel "IOPS (10K IOs/sec)"
set ylabel "Latency (ms)" offset -0.5, 0

# Read latency. Linear
if (1) {
  unset logscale y
	unset ytics
  set xtics nomirror tc rgb "black"
	set ytics nomirror tc rgb "black"
  set xrange [0:11]
	set yrange [0:12]

	col_base = 3
  plot FN_IN u ($2/1000):(column(col_base + 0) / 1000) w lp pt 7 ps 0.4 lc rgb "blue" not
}

# Read latency. Log scale. Whisker plot.
if (1) {
	set logscale y
	#unset yrange
  #set xrange [0:12000]
	set yrange [1:1000000]

	set ytics nomirror tc rgb "black" ( \
		"1"          1 \
	, "10"        10 \
	, "10^2"     100 \
	, "10^3"    1000 \
	, "10^4"   10000 \
	, "10^5"  100000 \
	, "10^6" 1000000 \
	)

	col_base = 3
  plot \
  FN_IN u ($2/1000):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)) w candlesticks lw 2 lc rgb "blue" not, \
  FN_IN u ($2/1000):(column(col_base + 4)):(column(col_base + 3)):(column(col_base + 8)):(column(col_base + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  FN_IN u ($2/1000):(column(col_base + 0)) w lp pt 7 ps 0.4 lc rgb "red" not

  # candlesticks
  # x  box_min  whisker_min  whisker_high  box_high
  # iops    5p           1p           99p       90p
  # 2        7            6            11         9
}

# Write latency. Log scale. Whisker plot.
if (1) {
	col_base = 14
  plot \
  FN_IN u ($2/1000):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)):(column(col_base + 5)) w candlesticks lw 2 lc rgb "blue" not, \
  FN_IN u ($2/1000):(column(col_base + 4)):(column(col_base + 3)):(column(col_base + 8)):(column(col_base + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  FN_IN u ($2/1000):(column(col_base + 0)) w lp pt 7 ps 0.4 lc rgb "red" not
}
