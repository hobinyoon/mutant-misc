#!/usr/bin/gnuplot
# Tested with gnuplot 4.6 patchlevel 4

FN_IN="data"
FN_OUT="db-1yr-cost-breakdown-by-storage-types.pdf"

set terminal pdfcairo enhanced size 2.6in, (2.6*0.80)in
set output FN_OUT

set bmargin at screen 0.320
set rmargin at screen 0.705

set xlabel "Storage device type" offset 0,-3.5
set ylabel "Cost (K$ / year)" offset 0.1,0

set border (1 + 2) lc rgb "#808080" front
set grid ytics back lc rgb "#808080"
set ytics nomirror scale 0.5,0 tc rgb "black" format "%.0f"
set tics front
set noxtics

X_MAX=3.5
set xrange [-0.5:X_MAX]
set yrange [0:]

set style fill solid 0.6 #noborder

COST_LOCAL_SSD=10129.59936
COST_OTHER=4816.43064

# calc "10129.59936 / (10129.59936 + 4816.43064)"
# ~0.67774515105349045867

# Other cost line
y0=COST_OTHER/1000.0
set arrow from -0.5,y0 to X_MAX,y0 nohead front lt 0 lw 6

x0=3.9
y0=(COST_OTHER + COST_LOCAL_SSD)/1000.0
LINE_WIDTH=2
LINE_COLOR="black"
set arrow from x0,0 to x0,y0 nohead front lc rgb LINE_COLOR lw LINE_WIDTH

x1=x0-0.05
x2=x0+0.05
y1=COST_OTHER/1000.0
set arrow from x1,0  to x2,0  nohead front lc rgb LINE_COLOR lw LINE_WIDTH
set arrow from x1,y1 to x2,y1 nohead front lc rgb LINE_COLOR lw LINE_WIDTH
set arrow from x1,y0 to x2,y0 nohead front lc rgb LINE_COLOR lw LINE_WIDTH

x3=x0+0.2
y2 = COST_OTHER / 1000.0 / 2 + 0.6
set label "CPU +\nMemory" at x3, y2
y3 = (COST_OTHER + (COST_LOCAL_SSD / 2)) / 1000.0
set label "Storage" at x3, y3

# boxxyerrorbars parameters
#   x  y  xlow  xhigh  ylow  yhigh
BOX_WIDTH=0.55
#set style fill transparent solid 0.3 border

# http://stackoverflow.com/questions/12427704/vary-point-color-based-on-column-value-for-multiple-data-blocks-gnuplot
set palette model RGB defined (\
  0 "#0000FF" \
, 1 "#006400" \
, 2 "#A52A2A" \
, 3 "#FF0000" \
, 4 "#808080" \
)

unset colorbox

plot \
FN_IN u 0:(0):1:0 w labels offset 0, -1.0 tc palette not, \
FN_IN u 0:(COST_OTHER/1000.0):($0-BOX_WIDTH/2):($0+BOX_WIDTH/2):(COST_OTHER/1000.0):(($2+COST_OTHER)/1000.0):0 \
  w boxxyerrorbars fs transparent solid 0.3 border palette lw 2 not, \
FN_IN u 0:(0/1000.0)         :($0-BOX_WIDTH/2):($0+BOX_WIDTH/2):(0)                :(COST_OTHER/1000.0)     :(4) \
  w boxxyerrorbars fs transparent solid 0.3 border palette lw 2 not, \

print sprintf("Created %s", FN_OUT)
