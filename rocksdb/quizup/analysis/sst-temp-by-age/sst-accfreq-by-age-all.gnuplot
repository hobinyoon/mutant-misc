# Tested with gnuplot 4.6 patchlevel 4

IN_SST_IDS = system("echo $IN_SST_IDS")
IN_DN = system("echo $IN_DN")
OUT_FN = system("echo $OUT_FN")

set print "-"
print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output OUT_FN

set border front lc rgb "#808080" back
set grid xtics ytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" #autofreq 0, 24*3600
set ytics nomirror tc rgb "black" #autofreq 0,2*60*60
set tics back

set xlabel "SSTables age (day)"
set ylabel "Access freq (cnt / 64MB / sec)"

#set logscale y
set yrange[0:]

plot for [i=1:words(IN_SST_IDS)] \
IN_DN . "/" . word(IN_SST_IDS, i) u ($1/24.0/3600):2 w l not
