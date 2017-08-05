# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEY)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border back lc rgb "#808080"
set grid xtics mxtics ytics back lc rgb "#808080"
set xtics nomirror tc rgb "black"
set mxtics 2
set ytics nomirror tc rgb "black"
#(\
#  "10^1"     10 \
#, "10^2"    100 \
#, "10^3"   1000 \
#, "10^4"  10000 \
#, "10^5" 100000 \
#)
set mytics
set tics front

# http://www.gnuplot.info/docs_4.2/gnuplot.html#x1-18600043.21.2
#set format y '10^{%T}'

set xlabel "Time (hour)" offset 0,0.3
set ylabel "Latency (ms)" offset 1.8,0

set size 1, 0.97
set key center at graph 0.5, 1.09 maxrows 1 samplen 0.5

set xrange[0:]
set yrange[0:70]

#set logscale y

plot \
FN_IN u (-1):(1) w p pt 2 pointsize 0.6 lc rgb "red"  lw 4 t "Insert", \
FN_IN u (-1):(1) w p pt 1 pointsize 0.6 lc rgb "blue" lw 4 t "Read", \
FN_IN u ($1/3600):($5 == -1 ? 1/0 : ($5 == 0 ? 1/0 : $5/1000)) w p pt 2 pointsize 0.3 lc rgb "red"  not, \
FN_IN u ($1/3600):($3 == -1 ? 1/0 : ($3 == 0 ? 1/0 : $3/1000)) w p pt 1 pointsize 0.3 lc rgb "blue" not
