#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 6

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output "block-dev-cost-seq-write-thrp-logxy.pdf"

set border lc rgb "#808080"
set grid xtics ytics mytics back lc rgb "#800880"
set xtics nomirror scale 1, 0.5 tc rgb "black"
set ytics nomirror scale 1, 0.5 autofreq 0,50 tc rgb "black"
set mxtics
set mytics 2
set tics back

set xlabel "Cost ($/GB/Month)"
set ylabel "Seq. write thrp. (MB/s)" offset 1.5,0

LINE_WIDTH=3

# Legend
x_c=0.1
y_t=0.92
y_b=y_t-0.20
set arrow from graph x_c, y_b to graph x_c, y_t nohead lw LINE_WIDTH lc rgb "black"
x_l=x_c-0.008
x_r=x_c+0.008
set arrow from graph x_l, y_t to graph x_r, y_t nohead lw LINE_WIDTH lc rgb "black"
set arrow from graph x_l, y_b to graph x_r, y_b nohead lw LINE_WIDTH lc rgb "black"
y3=(y_t+y_b)/2
set object circle at graph x_c, y3 size screen 0.008 fs solid noborder fc rgb "black"
set label "99%" at graph x_c, y_t offset 0.9,0
set label "Avg" at graph x_c, y3 offset 0.9,0
set label "1%"  at graph x_c, y_b offset 0.9,0

#colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

# http://stackoverflow.com/questions/12427704/vary-point-color-based-on-column-value-for-multiple-data-blocks-gnuplot
set palette model RGB defined (\
0 "#FF0000" \
, 1 "#A52A2A" \
, 2 "#006400" \
, 3 "#0000FF" \
)
unset colorbox

set logscale x
plot \
"data-cost-write" u 2:3:7:13:0 w yerrorbars pt 7 pointsize 0.3 lw LINE_WIDTH palette not, \
"data-cost-write" u 2:3:(strcol(1) ne "EBS st1" ? strcol(1) : "") w labels center offset 0, 1.0 not, \
"data-cost-write" u 2:3:(strcol(1) eq "EBS st1" ? strcol(1) : "") w labels center offset 0,-1.0 not
