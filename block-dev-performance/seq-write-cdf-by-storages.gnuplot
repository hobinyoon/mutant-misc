# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border back lc rgb "#808080"
set grid xtics ytics mytics back lc rgb "#808080"
set xtics mirror scale 0.5,0.25 tc rgb "black"
set ytics nomirror scale 0.5,0.25 format "%.1f" tc rgb "black"
set mytics 2
set tics back

set xlabel "Throughput (MB/s)" offset 0,0.5
set ylabel "CDF" offset 1.0 tc rgb "white"

colors="#FF0000 #A52A2A #006400 #0000FF #8B008B #6A5ACD"
#       red     darkgreen       blue    darkmagenta
#                       brown                   slateblue

set xrange[0:]

set size 1, 0.95
set key center at graph 0.5, 1.12 maxrows 1 width 1.0 samplen 0.8

# word() doesn't support quoted values until gnuplot 5.0
#
# key(i) = i == 1 ? "Local SSD" : \
# (i == 2 ? "EBS gp2" : \
# (i == 3 ? "EBS st1" : \
# (i == 4 ? "EBS sc1" : \
# "Unexpected" )))
key(i) = i == 1 ? "" : \
(i == 2 ? "" : \
(i == 3 ? "EBS st1" : \
(i == 4 ? "EBS sc1" : \
"Unexpected" )))

plot \
for [i=1:words(FN_IN)] word(FN_IN, i) u (-1):(0) w lines lc rgb word(colors, i) lw 6 t key(i), \
for [i=1:words(FN_IN)] word(FN_IN, i) u 1:2 w lines lc rgb word(colors, i) lw 2 not
