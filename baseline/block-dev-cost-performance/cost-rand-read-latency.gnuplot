#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 6

set terminal pdfcairo enhanced size 3in, (3*0.75)in
set output "block-dev-cost-rand-read-latency.pdf"

set border
set grid xtics ytics mytics back
set xtics nomirror scale 1, 0.5
set ytics nomirror scale 1, 0.5 autofreq 0,10
set mytics 2
set tics back

set xlabel "Cost ($/GB/Month)"
set ylabel "Random read latency (ms)" offset 1.5,0

set yrange[0:]

set size 0.96,1

set output "block-dev-cost-read-latency.pdf"
plot \
"data-cost-read" u 2:($3/1000):($7/1000):($13/1000) w yerrorbars pt 7 pointsize 0.3 lw 2 not, \
"data-cost-read" u 2:($3/1000):1 w labels left offset 0.7,0 not
