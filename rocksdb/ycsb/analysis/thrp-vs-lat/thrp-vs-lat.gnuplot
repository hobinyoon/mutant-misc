# Tested with gnuplot 4.6 patchlevel 6

FN_ROCKSDB_ST1 = system("echo $FN_ROCKSDB_ST1")
FN_ROCKSDB_LS = system("echo $FN_ROCKSDB_LS")
FN_MUTANT_LS_ST1 = system("echo $FN_MUTANT_LS_ST1")
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
    . "\n    (Blue: EBS Mag, Red: Local SSD)" \
    . "\n2: read latency (1p, 5p, 50p, 90p, 99p)" \
    . "\n3: write latency" \
    left front
  plot f(x) lc rgb "#F0F0F0" not
  unset label 1
}

set grid xtics mxtics ytics back lc rgb "#808080"
set border (1+2+4+8) back lc rgb "#808080"

# Read latency. Linear scale.
if (1) {
  set xlabel "IOPS (100K IOs/sec)"
  set ylabel "Latency (ms)" offset 1, 0
  unset logscale y
	unset ytics
  set xtics nomirror tc rgb "black"
	set ytics nomirror tc rgb "black"
  # TODO
  #set xrange [0:12]
  set xrange [0:6]
	set yrange [0:25]

	col_base0 = 3
  plot \
  FN_ROCKSDB_ST1   u ($2/10000):(column(col_base0 + 0) / 1000) w lp pt 7 ps 0.4 lc rgb "blue" not, \
  FN_ROCKSDB_LS    u ($2/10000):(column(col_base0 + 0) / 1000) w lp pt 7 ps 0.4 lc rgb "red" not, \
  FN_MUTANT_LS_ST1 u ($3/10000):(column(col_base0 + 1) / 1000) w lp pt 7 ps 0.4 lc rgb "purple" not
}

# Read latency. Log scale. Whisker plot.
if (1) {
  set xlabel "IOPS"
  set ylabel "Latency (ms)" offset -1, 0
	set logscale x
	set logscale y
	#unset yrange
  # TODO
  #set xrange [10/1.1:1200]
  set xrange [10/1.1:120]
	set yrange [1:1000000]

	set xtics nomirror tc rgb "black" ( \
	  "10K"   10 \
	, ""      20 \
	, ""      30 \
	, ""      40 \
	, ""      50 \
	, ""      60 \
	, ""      70 \
	, ""      80 \
	, ""      90 \
	, "100K" 100 \
	, ""     200 \
	, ""     300 \
	, ""     400 \
	, ""     500 \
	, ""     600 \
	, ""     700 \
	, ""     800 \
	, ""     900 \
	, "1M"  1000 \
	)

	set ytics nomirror tc rgb "black" ( \
		"1"          1 \
	, "10"        10 \
	, "10^2"     100 \
	, "10^3"    1000 \
	, "10^4"   10000 \
	, "10^5"  100000 \
	, "10^6" 1000000 \
	)

  # For RocksDB and Mutant
	col_base0 = 3
	col_base1 = 4

  plot \
  FN_ROCKSDB_ST1   u ($2/100):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)) w candlesticks lw 2 lc rgb "blue" not, \
  FN_ROCKSDB_ST1   u ($2/100):(column(col_base0 + 4)):(column(col_base0 + 3)):(column(col_base0 + 8)):(column(col_base0 + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  FN_ROCKSDB_ST1   u ($2/100):(column(col_base0 + 0)) w lp pt 7 ps 0.4 lc rgb "blue" not, \
  FN_ROCKSDB_LS    u ($2/100):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)) w candlesticks lw 2 lc rgb "red" not, \
  FN_ROCKSDB_LS    u ($2/100):(column(col_base0 + 4)):(column(col_base0 + 3)):(column(col_base0 + 8)):(column(col_base0 + 6)) w candlesticks whiskerbars lw 2 lc rgb "red" not, \
  FN_ROCKSDB_LS    u ($2/100):(column(col_base0 + 0)) w lp pt 7 ps 0.4 lc rgb "red" not, \
  FN_MUTANT_LS_ST1 u ($3/100):(column(col_base1 + 5)):(column(col_base1 + 5)):(column(col_base1 + 5)):(column(col_base1 + 5)) w candlesticks lw 2 lc rgb "purple" not, \
  FN_MUTANT_LS_ST1 u ($3/100):(column(col_base1 + 4)):(column(col_base1 + 3)):(column(col_base1 + 8)):(column(col_base1 + 6)) w candlesticks whiskerbars lw 2 lc rgb "purple" not, \
  FN_MUTANT_LS_ST1 u ($3/100):(column(col_base1 + 0)) w lp pt 7 ps 0.4 lc rgb "purple" not, \

  # candlesticks
  # x  box_min  whisker_min  whisker_high  box_high
  # iops    5p           1p           99p       90p
  # 2        7            6            11         9
}

# Write latency. Log scale. Whisker plot.
if (1) {
	col_base0 = 14
  plot \
  FN_ROCKSDB_ST1 u ($2/100):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)) w candlesticks lw 2 lc rgb "blue" not, \
  FN_ROCKSDB_ST1 u ($2/100):(column(col_base0 + 4)):(column(col_base0 + 3)):(column(col_base0 + 8)):(column(col_base0 + 6)) w candlesticks whiskerbars lw 2 lc rgb "blue" not, \
  FN_ROCKSDB_ST1 u ($2/100):(column(col_base0 + 0)) w lp pt 7 ps 0.4 lc rgb "blue" not, \
  FN_ROCKSDB_LS u ($2/100):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)):(column(col_base0 + 5)) w candlesticks lw 2 lc rgb "red" not, \
  FN_ROCKSDB_LS u ($2/100):(column(col_base0 + 4)):(column(col_base0 + 3)):(column(col_base0 + 8)):(column(col_base0 + 6)) w candlesticks whiskerbars lw 2 lc rgb "red" not, \
  FN_ROCKSDB_LS u ($2/100):(column(col_base0 + 0)) w lp pt 7 ps 0.4 lc rgb "red" not
}
