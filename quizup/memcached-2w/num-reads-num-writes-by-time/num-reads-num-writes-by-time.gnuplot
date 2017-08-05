#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN_R=".output/num-reads-by-time"
FN_IN_W=".output/num-writes-by-time"
FN_OUT=".output/quizup-num-reads-num-writes-by-time.pdf"

set print "-"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border back lc rgb "#808080"

set grid xtics mxtics ytics mytics back lc rgb "black"
set xtics nomirror tc rgb "black" autofreq 3*24*3600
set ytics nomirror tc rgb "black" autofreq 200
set mxtics 3
set mytics 2

#set format x "10^%T"
#set format y "10^%T"

set xdata time
set timefmt "%y%m%d-%H%M"
set format x "%d"

set xlabel "Time (day)" offset 0,-0.1
set ylabel "Number of accesses / sec" offset 1,0


set xrange ["160711-0600":"160727-2000"]
set yrange [0:1000]

plot \
FN_IN_R u 1:($2/1200.0) w l lw 2 lc rgb "red" t "Reads", \
FN_IN_W u 1:($2/1200.0) w l lw 2 lc rgb "blue" t "Writes", \

#FN_IN_R u 1:($2/1000.0) w l lw 2 lc rgb "red" t "Reads", \
#FN_IN_W u 1:($2/1000.0) w l lw 2 lc rgb "blue" t "Writes", \

#FN_IN_R u 1:($2/1000.0) w lp pt 7 pointsize 0.05 lw 2 lc rgb "red" t "Reads", \
#FN_IN_W u 1:($2/1000.0) w lp pt 7 pointsize 0.05 lw 2 lc rgb "blue" t "Writes", \

#FN_IN_R u 1:($2/1000.0) w p pt 7 pointsize 0.1 lc rgb "red" t "Reads", \
#FN_IN_W u 1:($2/1000.0) w p pt 7 pointsize 0.1 lc rgb "blue" t "Writes", \

print sprintf("Created %s", FN_OUT)
