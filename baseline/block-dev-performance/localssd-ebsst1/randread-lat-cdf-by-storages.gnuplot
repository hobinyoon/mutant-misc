# Tested with gnuplot 4.6 patchlevel 6

FN_IN_LS = system("echo $FN_IN_LS")
FN_IN_EST1 = system("echo $FN_IN_EST1")
FN_OUT = system("echo $FN_OUT")

set print "-"

set terminal pdfcairo enhanced size 2.1in, (2.1*0.90)in
set output FN_OUT

set border back lc rgb "#808080"
#set xtics nomirror tc rgb "black" font ",10"
set xtics nomirror tc rgb "black"
set mxtics 10
set ytics nomirror tc rgb "black" format "%.1f"
set grid xtics ytics mytics back lc rgb "#808080"

set xlabel "Latency (ms)"
set ylabel "CDF" offset 0.5,0

set label "Local\nSSD" at 0.1, 0.6 left tc rgb "red"
set label "EBS\nMag" at 2.5, 0.6 left tc rgb "blue"

set logscale x

set xrange [:100]

LW=2

plot \
FN_IN_LS   u ($1/1000):2 w l lc rgb "red"  lw LW not, \
FN_IN_EST1 u ($1/1000):2 w l lc rgb "blue" lw LW not
#FN_IN_LS   u ($1/1000):2 w l lc rgb "red"  t "Local SSD", \
#FN_IN_EST1 u ($1/1000):2 w l lc rgb "blue" t "EBS Mag"
