#!/bin/bash


echo '
set terminal postscript enhanced color eps
set style line 80 lt rgb "black"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"  # grey
set grid noxtics ytics back linestyle 81
#set border 11 back linestyle 80 #3
set border 3
set xtics nomirror
set ytics nomirror
set size 1,1
set style line 1 lt rgb "#A00000" lw 3 pt 6
set style line 2 lt rgb "#00A000" lw 3 pt 1
set style line 3 lt rgb "#5060D0" lw 3 pt 2
set style line 4 lt rgb "#F25900" lw 3 pt 9
set style line 5 lt rgb "#DD00AA" lw 3 pt 1
set style line 6 lt rgb "#AAF200" lw 3 pt 1
set style line 7 lt rgb "#B0D0FF" lw 3 pt 4

# set mxtics 10
# set mytics 10
# set key bottom right reverse Left width -8 font ",13.6"

#set terminal png size 1400,800
#set terminal postscript enhanced color eps

#set size 0.7

set xtics nomirror rotate by -45 scale 0 font ",14"

#set style histogram errorbars linewidth 1
set style histogram 
set style data histogram
set yrange[0:*]
set style fill solid 0.3 noborder

set output "figures/hash_comparison.eps"
set ylabel "Requests per second"
#set format y "%.0f%%"

plot "data/hash_comparison.out" using 2:xtic(1)  title "Throughput" ls 1

' | gnuplot
