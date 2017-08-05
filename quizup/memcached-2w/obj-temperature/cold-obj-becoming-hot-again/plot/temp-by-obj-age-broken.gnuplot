#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

#FN_IN = "../.output/temp-by-age-per-obj-lastupdatetime/229"
FN_IN = "data-229"
FN_OUT = "single-obj-temp-by-time-hot-cold-hotagain.pdf"

set print "-"

#set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
#set terminal pdfcairo enhanced size 4in, (2.3*0.85)in
set terminal pdfcairo enhanced size 8*0.9in, 2*0.9in
set output FN_OUT

set multiplot

set border (1 + 2 + 4) front lc rgb "#808080"
#set grid xtics ytics back lc rgb "black"

y1_color="black"

set ylabel "Reads / min" tc rgb y1_color offset 1,0

set xtics nomirror tc rgb "black" autofreq 10
set ytics nomirror tc rgb y1_color
set nomytics
set tics back

Y_MAX=30
Y2_MAX=110

set xrange[-0.5:99.5]
set yrange[0:Y_MAX]
set y2range[0:Y2_MAX]

L_PLOT_MAX_X=0.48
set rmargin at screen L_PLOT_MAX_X
# Bottom margin for the x label
B_MARGIN=0.22
set bmargin at screen B_MARGIN

set palette model RGB defined (\
0 y1_color \
, 1 "#FF0000" \
)
unset colorbox

TEMP_LW=3
BAR_WIDTH=1.0
FILL_RAIO=0.4

plot \
FN_IN u ($1-BAR_WIDTH/2):(0):($1-BAR_WIDTH/2):($1+BAR_WIDTH/2):(0):2:(0) w boxxyerrorbars axes x1y1 \
	fs solid FILL_RAIO border palette not, \
FN_IN u 1:3:(1) w l axes x1y2 lw TEMP_LW lc palette not, \

# Right plot
reset

set border (1 + 4 + 8) front lc rgb "#808080"
#set grid xtics ytics back lc rgb "black"

set y2label "Temperature" tc rgb "red" offset -1.5,0

set xtics nomirror tc rgb "black" autofreq 10
set y2tics nomirror tc rgb "red" offset -0.5,0
set tics back
set noytics

set xrange[714:815]
set yrange[0:Y_MAX]
set y2range[0:Y2_MAX]

R_PLOT_MIN_X = L_PLOT_MAX_X + 0.01
set lmargin at screen R_PLOT_MIN_X
set rmargin at screen 0.93
set bmargin at screen B_MARGIN

set palette model RGB defined (\
0 y1_color \
, 1 "#FF0000" \
)
unset colorbox

# Broken line markers and x label
if (1) {
	y0=B_MARGIN
	y_delta=0.02
	x_delta=0.004
	y1=0.925
	set arrow from screen L_PLOT_MAX_X-x_delta,y0-y_delta to screen L_PLOT_MAX_X+x_delta,y0+y_delta lw 2 lc rgb "#808080" nohead
	set arrow from screen L_PLOT_MAX_X-x_delta,y1-y_delta to screen L_PLOT_MAX_X+x_delta,y1+y_delta lw 2 lc rgb "#808080" nohead
	set arrow from screen R_PLOT_MIN_X-x_delta,y0-y_delta to screen R_PLOT_MIN_X+x_delta,y0+y_delta lw 2 lc rgb "#808080" nohead
	set arrow from screen R_PLOT_MIN_X-x_delta,y1-y_delta to screen R_PLOT_MIN_X+x_delta,y1+y_delta lw 2 lc rgb "#808080" nohead

	set label "Object age (min)" at screen 0.5, B_MARGIN-0.17 center tc rgb "black"
}

plot \
FN_IN u ($1-BAR_WIDTH/2):(0):($1-BAR_WIDTH/2):($1+BAR_WIDTH/2):(0):2:(0) w boxxyerrorbars axes x1y1 \
	fs transparent solid FILL_RAIO border palette not, \
FN_IN u 1:3:(1) w l axes x1y2 lw TEMP_LW lc palette not, \

print sprintf("Created %s", FN_OUT)
