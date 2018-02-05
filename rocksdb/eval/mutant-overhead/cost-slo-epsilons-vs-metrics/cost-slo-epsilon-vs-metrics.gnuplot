# Tested with gnuplot 4.6 patchlevel 6

FN_CSE_VS_ALL = system("echo $FN_CSE_VS_ALL")
LINEAR_REG_PARAMS = system("echo $LINEAR_REG_PARAMS")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("LINEAR_REG_PARAMS=%s", LINEAR_REG_PARAMS)

set terminal pdfcairo enhanced size 2.6in, (2.3*0.85)in
set output FN_OUT

#X_MIN = 0.01 / 1.5
X_MIN = -0.01
X_MAX = 0.21

# Storage unit cost
if (1) {
  reset

  cost_slo = 0.3

  set xlabel "SSTable no-organization\nrange length (%)"
  set ylabel "Storage cost / Cost SLO"
  #set y2label "$/GB/month" offset -0.5,0
  set y2label "Storage cost ($/GB/mo)" offset -0.5,0
  #set xtics nomirror tc rgb "black" format "%0.2f" autofreq 0,0.05
  set xtics nomirror tc rgb "black" (\
    "0" 0, \
    "5" 0.05, \
    "10" 0.10, \
    "15" 0.15, \
    "20" 0.20 \
    )
  set nomxtics

  set ytics nomirror tc rgb "black" format "%0.2f" autofreq 0,0.02
  set mytics 2

  set y2tics nomirror tc rgb "black" format "%0.2f" autofreq 0,0.01

  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  y_min = 0.98
  y_max = 1.09
  set yrange[y_min:y_max]
  y2_min = y_min * cost_slo
  y2_max = y_max * cost_slo
  set y2range[y2_min:y2_max]

  set rmargin screen 0.79

  slope = word(LINEAR_REG_PARAMS, 1) / cost_slo
  y0_lr = word(LINEAR_REG_PARAMS, 2) / cost_slo
  y0_upper_bound = word(LINEAR_REG_PARAMS, 3) / cost_slo

  x0 = 0
  x1 = 0.20

  set xrange[x0:x1]

  # Linear regression line
  if (1) {
    y0 = y0_lr
    y1 = (slope * x1) + y0
    set arrow from x0, y0 to x1, y1 nohead lc rgb "blue" lw 6 lt 0 back

    x2 = x1 * 1.03
    y2 = (slope * x2) + y0
    #set label "Linear\nregression" at x2, y2 offset 0,0.5 left tc rgb "black" front
    #set label "LR" at x2, y2 left tc rgb "black" front
  }

  # Cost error upper bound
  if (1) {
    y0 = y0_upper_bound
    y1 = (slope * x1) + y0
    #set arrow from x0, y0 to x1, y1 nohead lc rgb "#808080" lw 1

    set object 1 polygon from \
      x0, y0 \
      to x1, y1 \
      to x1, 1 \
      to x0, 1 \
      to x0, y0 \
      fs transparent solid 0.1 noborder fc rgb "blue" back
  }

#  # This varies by (depends on) the storage cost SLO and the base storage costs.
#  #   0.3, [0.045, 0.528]
#  #   If the cost SLO were lower than 0.3, I am guessing we would have gotten a different curve, a less stiffer curve.
#
#  set arrow from 0, 0.3 to X_MAX, 0.3 nohead lc rgb "black" lw 6 lt 0
#  set label "Cost\nSLO" at X_MAX, 0.3 center offset 2.5,0.5 tc rgb "black" front

  plot \
  FN_CSE_VS_ALL u 1:2 axes x1y2 w p pt 7 ps 0.0001 lc rgb "white" not, \
  FN_CSE_VS_ALL u 1:($2/cost_slo) w p pt 7 ps 0.3 lc rgb "red" not
}

w_2 = 0.005 / 2

# Total SSTable size migrated
if (1) {
  reset
  #set xlabel "Cost SLO {/Symbol e} (%)"
  set xlabel "SSTable no-organization\nrange length (%)"
  set ylabel "SSTables migrated (GB)"
  set xtics nomirror tc rgb "black" (\
    "0" 0, \
    "5" 0.05, \
    "10" 0.10, \
    "15" 0.15, \
    "20" 0.20 \
    )
  set nomxtics
  set ytics nomirror tc rgb "black" #format "%0.2f" autofreq 0,0.02
  set mytics 2
  set grid xtics ytics front lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  set yrange[0:]

  # Legend
  if (1) {
    x0 = 0.61
    y0 = 0.87
    x1 = x0 + 0.1
    y_height = 0.06
    y1 = y0 + y_height
    set obj rect from graph x0,y0 to graph x1,y1 fc rgb "#8080FF" fs solid noborder front
    x2 = x1 + 0.04
    y2 = (y0+y1)/2
    set label "To slow" at graph x2, y2

    y0 = y0 - 0.12
    y1 = y0 + y_height
    set obj rect from graph x0,y0 to graph x1,y1 fc rgb "#FF8080" fs solid noborder front
    y2 = (y0+y1)/2
    set label "To fast" at graph x2, y2
  }

  if (1) {
    plot \
    FN_CSE_VS_ALL u 1:(0):($1-w_2):($1+w_2):(0):16        w boxxyerrorbars lc rgb "#8080FF" fs solid not, \
    FN_CSE_VS_ALL u 1:16 :($1-w_2):($1+w_2):16 :($16+$17) w boxxyerrorbars lc rgb "#FF8080" fs solid not
    # boxxyerrorbars: x y xlow xhigh ylow yhigh
  }

  # So the temperature-triggered single-sstable migration is kind of unnecessary.
  #   The chart below makes it very clear, but didn't want to present.
  if (0) {
    # With lp
    if (0) {
      plot \
      FN_CSE_VS_ALL u 1:16 w lp pt 7 ps 0.3 lc rgb "#8080FF" not, \
      FN_CSE_VS_ALL u 1:17 w lp pt 7 ps 0.3 lc rgb "#FF8080" not
    }

    # Box plot
    #   The plot is too dense.
    if (0) {
      plot \
      FN_CSE_VS_ALL u 1:(0):($1-0.003):($1-0.001):(0):16 w boxxyerrorbars lc rgb "#8080FF" fs solid not, \
      FN_CSE_VS_ALL u 1:(0):($1+0.001):($1+0.003):(0):17 w boxxyerrorbars lc rgb "#FF8080" fs solid not
      # boxxyerrorbars: x y xlow xhigh ylow yhigh
    }
  }
}

# Total SSTable size compacted
if (1) {
  reset
  #set xlabel "Cost SLO {/Symbol e} (%)"
  set xlabel "SSTable no-organization\nrange length (%)"
  set ylabel "SSTables compacted (GB)" offset 1,0
  set xtics nomirror tc rgb "black" (\
    "0" 0, \
    "5" 0.05, \
    "10" 0.10, \
    "15" 0.15, \
    "20" 0.20 \
    )
  set nomxtics
  set ytics nomirror tc rgb "black" autofreq 0,50
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  set yrange[0:]

  set rmargin screen 0.79

  # Legend
  if (1) {
    x0 = 1.03
    y0 = 0.7
    y1 = 0.19
    x_w2 = 0.01
    set arrow from graph x0, y0 to graph x0, y1 nohead
    set arrow from graph x0-x_w2, y0 to graph x0+x_w2, y0 nohead
    set arrow from graph x0-x_w2, y1 to graph x0+x_w2, y1 nohead
    y_m = (y0 + y1) / 2
    x1 = x0 + 0.03
    set label "Regular\ncomp." at graph x1, y_m offset 0,0.5

    y0 = y1
    y1 = 0
    set arrow from graph x0, y0 to graph x0, y1 nohead
    set arrow from graph x0-x_w2, y0 to graph x0+x_w2, y0 nohead
    set arrow from graph x0-x_w2, y1 to graph x0+x_w2, y1 nohead
    y_m = (y0 + y1) / 2
    set label "Comp.-\nmigr." at graph x1, y_m offset 0,0.5
  }

  plot \
  FN_CSE_VS_ALL u 1:(0)      :($1-w_2):($1+w_2):(0)      :12        w boxxyerrorbars lc rgb "#8080FF" fs solid not, \
  FN_CSE_VS_ALL u 1:12       :($1-w_2):($1+w_2):12       :($12+$13) w boxxyerrorbars lc rgb "#FF8080" fs solid not, \
  FN_CSE_VS_ALL u 1:($12+$13):($1-w_2):($1+w_2):($12+$13):10        w boxxyerrorbars lc rgb "#808080" fs solid not
}
