# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080"
set grid xtics ytics mxtics mytics back lc rgb "#808080"
set xtics nomirror autofreq 0,50 tc rgb "black"
set mxtics 2
set ytics nomirror autofreq 0,50 tc rgb "black"
set mytics 2
set tics front

set xlabel "Request #"
set ylabel "Throughput (MB/s)" offset 1,0

colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

set xrange[:200]
set yrange[0:]
#set key right bottom

# Manual position of keys. set key above gives the graph area too short
# - http://stackoverflow.com/questions/13788764/gnuplot-add-key-outside-plot-without-resizing-plot
set size 1, 0.9
set key center at graph 0.5, 1.15 maxrows 2 samplen 0.5 width -1.5

key(i) = i == 1 ? "Local SSD" : \
(i == 2 ? "EBS gp2" : \
(i == 3 ? "EBS st1" : \
(i == 4 ? "EBS sc1" : \
"Unexpected" )))

plot \
for [i=1:words(FN_IN)] word(FN_IN, i) u 0:(-1) w p pt 7 pointsize 0.5 lc rgb word(colors, i) t key(i), \
for [i=1:words(FN_IN)] word(FN_IN, i) u 0:1 w p pt 7 pointsize 0.15 lc rgb word(colors, i) not
