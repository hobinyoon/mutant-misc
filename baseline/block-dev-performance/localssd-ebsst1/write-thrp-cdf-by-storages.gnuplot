# Tested with gnuplot 4.6 patchlevel 6

FN_IN_LS = system("echo $FN_IN_LS")
FN_IN_EST1 = system("echo $FN_IN_EST1")
FN_OUT = system("echo $FN_OUT")

set print "-"

set terminal pdfcairo enhanced size 2.1in, (2.1*0.85)in
set output FN_OUT

set border back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0,50
#set mxtics 10
set ytics nomirror tc rgb "black" format "%.1f"
set grid xtics ytics mytics back lc rgb "#808080"

set xlabel "Throughput (MB/sec)"
set ylabel "CDF" offset 0.5,0 tc rgb "white"

set label "EBS\nMag"   at 105, 0.6 right tc rgb "blue"
set label "Local\nSSD" at 175, 0.6 left  tc rgb "red"

#set logscale x

set xrange [0:]

LW=2

plot \
FN_IN_LS   u 1:2 w l lc rgb "red"  lw LW not, \
FN_IN_EST1 u 1:2 w l lc rgb "blue" lw LW not
#FN_IN_LS   u 1:2 w l lc rgb "red"  t "Local SSD", \
#FN_IN_EST1 u 1:2 w l lc rgb "blue" t "EBS Mag"
