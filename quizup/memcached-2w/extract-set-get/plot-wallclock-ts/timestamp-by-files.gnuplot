# Tested with gnuplot 4.6 patchlevel 4

DTS = system("echo $DTS")
FNS = system("echo $FNS")
FN_OUT = system("echo $FN_OUT")

set print "-"

set xdata time
set timefmt "%d%H%M%S"
set format x "%d"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

plot \
for [i=1:words(FNS)] word(FNS, i) every 40000 u ((word(DTS, i))+$0*1000):1 w lp pt 7 pointsize 0.1 not

##set grid xtics mxtics back lc rgb "#808080"
##set grid back
#set border front lc rgb "#808080"
#set xtics nomirror scale 0.5,0.25 out tc rgb "black" autofreq 0,20 * 60
#set nomxtics
