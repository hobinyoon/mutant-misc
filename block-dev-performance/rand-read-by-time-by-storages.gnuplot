# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
KEYS = system("echo $KEYS")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEYS)

set terminal pdfcairo enhanced size 3in, (3*0.75)in
set output FN_OUT

set border back
set grid xtics mxtics ytics back
set xtics nomirror scale 0.5,0.25 #autofreq 0,200
set mxtics 2
set ytics nomirror scale 0.5,0 #autofreq 0,50
set tics back

set xlabel "Request # (in K. by time)"
set ylabel "Latency (ms)" offset 1.5,0

colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

set logscale y
set yrange [0.1:]
set xrange [0:]

# Manual position of keys. set key above gives the graph area too short
# - http://stackoverflow.com/questions/13788764/gnuplot-add-key-outside-plot-without-resizing-plot
set size 1, 0.9
set key center at graph 0.5, 1.15 maxrows 2 samplen 0.5

set samples 1000

# For the legend, plot at 0, 0.01, which is out of the range.

set style circle radius screen 0.0015

plot \
for [i=1:words(FN_IN)] \
word(FN_IN, i) u (0):(0.01) w points pt 7 pointsize 0.5 lc rgb word(colors, i) t word(KEYS, i), \
for [i=1:words(FN_IN)] \
word(FN_IN, i) u ($0/1000):($1/1000.0) w circles fs solid 0.6 noborder fc rgb word(colors, i) not

#, \
#for [i=1:words(FN_IN)] \
#word(FN_IN, i) u ($0/1000):($1/1000.0) w l smooth bezier lw 3 lc rgb word(colors, i) not
