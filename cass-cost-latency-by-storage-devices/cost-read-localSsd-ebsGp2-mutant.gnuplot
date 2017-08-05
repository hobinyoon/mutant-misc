#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN="data-cost-read-lat-localSsd-ebsGp2-mutant"
FN_OUT="cost-read-localSsd-ebsGp2-mutant.pdf"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set print "-" 

set border lc rgb "#808080"
set grid xtics ytics back lc rgb "#808080"
set xtics nomirror tc rgb "black" autofreq 0,0.1
set ytics nomirror tc rgb "black"
set mxtics
set mytics
set tics back

set xlabel "Cost ($/GB/Month)"
set ylabel "Read latency (ms)" offset 1.0,0

LINE_WIDTH=4

# Legend
x_c=0.78
y_t=0.92
y_b=y_t-0.20
LC="#404040"
set arrow from graph x_c, y_b to graph x_c, y_t nohead lw LINE_WIDTH lc rgb LC
x_l=x_c-0.008
x_r=x_c+0.008
set arrow from graph x_l, y_t to graph x_r, y_t nohead lw LINE_WIDTH lc rgb LC
set arrow from graph x_l, y_b to graph x_r, y_b nohead lw LINE_WIDTH lc rgb LC
y3=(y_t+y_b)/2
set object circle at graph x_c, y3 size screen 0.008 fs solid noborder fc rgb LC
set label "99%" at graph x_c, y_t offset 0.9,0
set label "Avg" at graph x_c, y3 offset 0.9,0
set label "1%"  at graph x_c, y_b offset 0.9,0

#colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

# http://stackoverflow.com/questions/12427704/vary-point-color-based-on-column-value-for-multiple-data-blocks-gnuplot
set palette model RGB defined (\
0 "#FF0000" \
, 2 "#0000FF" \
)
unset colorbox

set xrange[0:]
set yrange[0:]

plot \
FN_IN u 2:($3/1000):($4/1000):($5/1000):0 w yerrorbars pt 7 pointsize 0.3 lw LINE_WIDTH palette not, \
FN_IN u 2:($3/1000):(strcol(1) ne "EBS SSD" ? strcol(1) : "") w labels      offset 0.0,-1 not, \
FN_IN u 2:($3/1000):(strcol(1) eq "EBS SSD" ? strcol(1) : "") w labels left offset 0.7,0 not

# You can't get the output file size here. It returns 0. The file must not be closed yet.
#   cmd="wc -c < " . FN_OUT
#   system(cmd)
print sprintf("Created %s", FN_OUT)
