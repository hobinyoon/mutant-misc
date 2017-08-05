#!/usr/bin/gnuplot

# Tested with gnuplot 4.6 patchlevel 4

FN_OUT = system("echo $FN_OUT")

set print "-"

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output "heat-map-legend.pdf"

# Legend
x_l=0.05
x_r=x_l + 0.05
y_t=0.94
y_height=0.5
y_b=y_t - y_height

# http://stackoverflow.com/questions/12875486/what-is-the-algorithm-to-create-colors-for-a-heatmap
# 0    red    #FF0000 16711680
# 0.25 yellow #FFFF00 16776960
# 0.5  green  #00FF00 65280
# 0.75 cyan   #00FFFF 65535
# 1    blue   #0000FF 255
color0(i)=(i < 0.25 ? (16711680 + int((i / 0.25) * 255.9999999) * 256) : \
i < 0.5  ? (65280 + int((1 - (i - 0.25) / 0.25) * 255.9999999) * 256 * 256) : \
i < 0.75 ? (65280 + int((i - 0.50) / 0.25 * 255.9999999)) : \
           (255 + int((1 - (i - 0.75) / 0.25) * 255.9999999) * 256))
color1(i)=color0(1.0-i)

# Play with this if you see horizontal stripes
y_overlap=0.8
y_unit = y_height / 256.0

do for [i=0:255] {
	set object (i+1) rect from graph x_l, graph y_t - y_unit * (i+1+y_overlap) \
	to graph x_r, graph y_t - y_unit * i \
	fs solid 1.0 noborder fc rgb color1((255 - i) / 255.0) lw 0.1 front
}

set object rect from graph x_l, graph y_t - y_unit * (255+1+y_overlap) \
to graph x_r, graph y_t - y_unit * (0) \
fs transparent solid 0.0 border fc rgb "black" front

f(x)=x
plot f(x) not
