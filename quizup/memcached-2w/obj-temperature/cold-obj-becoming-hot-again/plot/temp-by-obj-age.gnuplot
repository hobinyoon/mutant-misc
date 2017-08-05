#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

#FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/269"
#FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/265"
#FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/921"
#FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/444"
FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/229"
FN_OUT = "single-obj-temp-by-time.pdf"

set print "-"

#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set terminal pdfcairo enhanced size 32in, (2.3*0.85)in
set output FN_OUT

set border (1 + 2 + 4) front lc rgb "#808080"

#set grid xtics mxtics ytics back lc rgb "black"

set xlabel "Object age" offset 0,0.1
set ylabel "Reads/min" tc rgb "blue" offset 1,0
#set y2label "Temperature" tc rgb "red"

set xtics nomirror tc rgb "black" rotate by -90 autofreq 60
set ytics nomirror tc rgb "blue"
#set y2tics nomirror tc rgb "red"
set nomytics
set tics back

set xrange[-0.5:]
#set yrange[0:60]
#set y2range[0:160]

# TODO: find a different example with 2 peaks. 3 is distracting.  and the reads
# last for quite a while after the second peak, cause those are what are gonna
# benefit from the record re-insertions.

BAR_WIDTH=1.0

# TODO: thinker line

set palette model RGB defined (\
0 "#0000FF" \
, 1 "#FF0000" \
)
unset colorbox

plot \
FN_IN u ($1-BAR_WIDTH/2):(0):($1-BAR_WIDTH/2):($1+BAR_WIDTH/2):(0):2:(0) w boxxyerrorbars axes x1y1 \
	fs transparent solid 0.5 border palette not, \
FN_IN u 1:3:(1) w l axes x1y2 lw 2 lc palette not, \

print sprintf("Created %s", FN_OUT)
