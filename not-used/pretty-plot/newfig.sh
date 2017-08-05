#!/bin/bash

DATA="./output/"
OUTDIR="./"

# Gnuplot terminal settings
out_format="pdf"        # png/pdf
plotsize="5,3" #"750,450"      # 5,3 for pdf
fontsize=21 #13             # 7 for pdf
linewidth=4 #2             # 4 for pdf

function doplot {
    # remove the last comma
    plot=$(echo $plot | sed 's/\(.*\),/\1/')
    echo "Plotting $out"
    echo ' 
    set terminal '$out_format'cairo enhanced font "Gill Sans, '$fontsize'" linewidth '$linewidth' rounded size '$plotsize'
    set style line 80 lt rgb "black"
    set style line 81 lt 0  # dashed
    set style line 81 lt rgb "#808080"  # grey
    set grid back linestyle 81
    set border 3 back linestyle 80
    set xtics nomirror
    set ytics nomirror
    set size 1,1
#    set style line 1 lt rgb "#DD00AA" lw 3 pt 1
#    set style line 2 lt rgb "#AAF200" lw 3 pt 1
#    set style line 3 lt rgb "#00A000" lw 3 pt 6
#    set style line 4 lt rgb "#5060D0" lw 3 pt 2
#    set style line 5 lt rgb "#F25900" lw 3 pt 9
#    set style line 6 lt rgb "#B0D0FF" lw 3 pt 4
    set style line 1 lt rgb "#005F00" lw 3 pt 1
    set style line 2 lt rgb "#008F00" lw 3 pt 1
    set style line 3 lt rgb "#00aF00" lw 3 pt 6
    set style line 4 lt rgb "#00bF00" lw 3 pt 2
    set style line 5 lt rgb "#00dF00" lw 3 pt 9
    set style line 6 lt rgb "#00FF00" lw 3 pt 4
    set style line 7 lt 4 lc rgb "#A00000" lw 3 pt 5
    set style line 8 lw 2
    set style line 9 lw 2
    set mxtics 10
    set mytics 10
    set key bottom right reverse Left width -8 font ",13.6"
    set xlabel "'$xlabel'" offset 0,.5
    set ylabel "'$ylabel'" offset .5,0
    '$options'

    set output "'$OUTDIR/$out'.'$out_format'"
    '$plot'
    ' | gnuplot -persist
}

function newplot {
    plot="plot "
    line=1
    options=""
}

function addline {
    cols='($0/(60000.0/20.0)):(100*$1)' # XXX: right number
    plot=$( echo $plot '"'$data'" using '$cols' every '$every' with lines ls '$line' title "'$title'",')
    ((line++))
}

### Plot percentiles
newplot
every=1
ylabel="Hit rate (%)"
xlabel="Cache size (MB)"
threshold=460
#options='set arrow from '$threshold', graph 0 to '$threshold', graph 1 nohead ls 1 lt rgb "#A9A9A9"'
#options=$options'; set xtics ( "x" '$threshold', "2x" 2*'$threshold', "3x" 3*'$threshold' ); set xrange[80:927];'
options='set xrange[0:22]'

data="$DATA/rounder__bits=2.txt"
title="Rounder B=4 (98.0\% acc.)"
addline

data="$DATA/rounder__bits=3.txt"
title="Rounder B=8 (98.8\% acc.)"
addline

data="$DATA/rounder__bits=4.txt"
title="Rounder B=16 (99.1\% acc.)"
addline

data="$DATA/rounder__bits=5.txt"
title="Rounder B=32 (99.4\% acc.)"
addline

data="$DATA/rounder__bits=6.txt"
title="Rounder B=64 (99.4\% acc.)"
addline

data="$DATA/rounder__bits=7.txt"
title="Rounder B=128 (99.4\% acc.)"
addline

#ycol=9
#title="99% latency"
#addline

data="$DATA/naive__bits=3.txt"
title="Mattson (True LRU)"
addline


plot="$(echo $plot "'$DATA/memcached-output.txt' using 1:2 with points lc rgb '#000098' ps 2.0 pt 6 title 'Measured memcached hit rate'", )"

out="memcached-accuracy"
doplot
