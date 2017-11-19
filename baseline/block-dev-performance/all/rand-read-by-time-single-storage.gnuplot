# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
KEY = system("echo $KEY")
FN_OUT = system("echo $FN_OUT")
KEY_IDX = system("echo $KEY_IDX")
KEY_IDX = KEY_IDX + 0
Y_LABEL_COLOR = system("echo $Y_LABEL_COLOR")

set print "-"
print sprintf(KEY)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080"
set grid xtics mxtics ytics back lc rgb "#808080"
set xtics nomirror autofreq 0,2 tc rgb "black"
set mxtics 2
set ytics nomirror tc rgb "black"
set mytics
set tics front

set xlabel "Request # (in K)"
set ylabel "Latency (ms)" offset 2,0 tc rgb Y_LABEL_COLOR

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

less_dense_y_min(k) = k == 1 ? 0 : \
(k == 2 ? 0.38 : \
(k == 3 ? 0.4 : \
(k == 4 ? 7 : \
0 \
)))

less_dense_y_max(k) = k == 1 ? 0.3 : \
(k == 2 ? 0.6 : \
(k == 3 ? 40 : \
(k == 4 ? 50 : \
0 \
)))

# Reduce the file size by making the strip of dense points less dense by 1/3
# while keeping the graph look the same.
dot_y(x, y) = (less_dense_y_min(KEY_IDX) < y && y < less_dense_y_max(KEY_IDX)) ? \
  ((sprintf("%d", (x * 1000)) + 0) % 3 == 0 ? y : 1/0) \
  : (y)

plot \
FN_IN u (0):($0 == 1 ? 0.01 : 1/0) w points pt 7 pointsize 0.5 lc rgb word(colors, KEY_IDX) t KEY, \
FN_IN u ($0/1000.0):(dot_y($0/1000.0, $1/1000.0)) w points pt 7 pointsize 0.07 lc rgb word(colors, KEY_IDX) not
