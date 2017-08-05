# Tested with gnuplot 4.6 patchlevel 6

FN_IN_MEMT = system("echo $FN_IN_MEMT")
FN_IN_SST = system("echo $FN_IN_SST")
FN_IN_SST_LEVEL_SEP = system("echo $FN_IN_SST_LEVEL_SEP")
FN_IN_SST_NUM_READS = system("echo $FN_IN_SST_NUM_READS")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEYS)

#----------------------------------------------------------
# Get data range
# Bottom plot
set terminal unknown
set xdata time
set timefmt "%y%m%d-%H%M%S"
set format x "%H:%M"
plot \
FN_IN_MEMT u 2:($1/1024/1024/1024):2:3:($1/1024/1024/1024):($1/1024/1024/1024+$4/1024/1024) w boxxyerrorbars not
b_X_MIN=GPVAL_DATA_X_MIN
b_X_MAX=GPVAL_DATA_X_MAX
b_Y_MAX=GPVAL_DATA_Y_MAX

# Top plot
set terminal unknown
plot \
FN_IN_SST u 4:12:4:5:12:($12 + $6) w boxxyerrorbars not
t_Y_MIN=GPVAL_DATA_Y_MIN
t_Y_MAX=GPVAL_DATA_Y_MAX

print sprintf("b_X_MAX=%d b_Y_MAX=%d t_Y_MIN=%d t_Y_MAX=%d", b_X_MAX, b_Y_MAX, t_Y_MIN, t_Y_MAX)

#----------------------------------------------------------
# Bottom chart
#set terminal pdfcairo enhanced size 10in, 5in
set terminal pdfcairo enhanced size 10in, 10in
set output FN_OUT

set border back lc rgb "#808080"
set grid xtics mxtics ytics mytics back lc rgb "#808080"
set xtics scale 0.5,0.25 tc rgb "black" #autofreq 0,200
set mxtics 2
set ytics scale 0.5,0 format "%3.0f" tc rgb "black" autofreq 0,1
set mytics 2
set tics back

set xlabel "Time"
set ylabel "Memtables (in Java\nprocess address space)"

# Check if the fractional seconds are plotted correctly
#set format x "%M%.1S"
#set xrange["160920-165656.166":"160920-165656.966"]

set multiplot

set size 1, 0.10
set origin 0,0

set xrange[b_X_MIN:b_X_MAX]
set yrange[0:b_Y_MAX]

plot \
FN_IN_MEMT u 2:($1/1024/1024/1024):2:3:($1/1024/1024/1024):($1/1024/1024/1024+$4/1024/1024) w boxxyerrorbars fs solid lc rgb "#FF8080" not
# Note: probably want to use a filled curve.

reset

# Top chart

set size 1, 0.78
# Play with this to make each SSTable height about the same as Memtable
set size 1, 0.90

#set origin 0,0.22
set origin 0,0.09

set border back lc rgb "#808080"
set grid xtics mxtics front lc rgb "#808080"
set xtics scale 0.5,0.25 tc rgb "black"
set mxtics 2
# Invisible, white tics to align the top plot with the bottom one
set ytics scale 0,0 format "%3.0f" tc rgb "white" ("000" 0)
set tics front

set ylabel "SSTables\n(grouped by levels)"
set noxlabel

set xdata time
set timefmt "%y%m%d-%H%M%S"
set format x ""

set xrange[b_X_MIN:b_X_MAX]
set yrange[t_Y_MIN:t_Y_MAX]

plot \
FN_IN_SST u 4:12:4:5:12:($12 + $6) w boxxyerrorbars fs solid 0.15 noborder lc rgb "black" not, \
FN_IN_SST_NUM_READS u 2:4 w p pt 7 pointsize 0.05 lc rgb "red" not, \
FN_IN_SST u 4:($12+($6/2)):1 w labels left not, \
FN_IN_SST_LEVEL_SEP u (b_X_MIN):2:1 w labels offset -1,0 not, \
FN_IN_SST_LEVEL_SEP u (b_X_MIN):3:(b_X_MAX):(0) w vectors lt 0 lc rgb "black" not

# Not showing desc for now. Some are too long.
#FN_IN_SST u 4:($12+($6/2)):13 w labels left not, \

unset multiplot

# xerrorbars:     x y xlow xhigh
# boxxyerrorbars: x y xlow xhigh ylow yhigh
