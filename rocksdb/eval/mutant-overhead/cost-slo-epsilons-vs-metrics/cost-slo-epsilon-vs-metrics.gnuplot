# Tested with gnuplot 4.6 patchlevel 6

FN_CSE_VS_ALL = system("echo $FN_CSE_VS_ALL")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf("NUM_STGDEVS=%d", NUM_STGDEVS)

set terminal pdfcairo enhanced size 2.8in, (2.3*0.85)in
set output FN_OUT

LMARGIN=0.25
RMARGIN=0.86
#X_MIN = 0.01 / 1.5
X_MIN = -0.01
X_MAX = 0.21

# Storage unit cost
if (1) {
  reset
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "Storage unit cost\n($/GB/month)" offset 0.4,0
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" format "%0.2f" autofreq 0,0.02
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  # TODO: set manual mxtics
  if (1) {
  }

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0.28:0.36]

  # Align the stacked plots
  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  set arrow from X_MIN, 0.3 to X_MAX, 0.3 nohead lc rgb "blue" lw 5 lt 0 front
  set label "Cost\nSLO" at X_MAX, 0.3 offset 1,0.5 tc rgb "blue" front

  plot \
  FN_CSE_VS_ALL u 1:2 w p pt 7 ps 0.3 lc rgb "red" not
}

# Total SSTable size migrated
if (1) {
  reset
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "SSTables migrated (GB)"
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" #format "%0.2f" autofreq 0,0.02
  set mytics 2
  set grid xtics ytics front lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0:]

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  w_2 = 0.005 / 2

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
  set xlabel "Cost SLO {/Symbol e}"
  set ylabel "SSTables compacted (GB)"
  set xtics nomirror tc rgb "black"
  set nomxtics
  set ytics nomirror tc rgb "black" autofreq 0,50
  set mytics 2
  set grid xtics ytics back lc rgb "#808080"
  set border back lc rgb "#808080" back

  set xrange[X_MIN:X_MAX]
  #set logscale x
  set yrange[0:]

  set lmargin screen LMARGIN
  set rmargin screen RMARGIN

  # TODO: Legend

  plot \
  FN_CSE_VS_ALL u 1:(0   + 2):(0):($12-2) w vectors nohead lc rgb "#8080FF" lw 10 not, \
  FN_CSE_VS_ALL u 1:($12 + 2):(0):($13-2) w vectors nohead lc rgb "#FF8080" lw 10 not, \
  FN_CSE_VS_ALL u 1:($12 + $13 + 2):(0):($10 - $11 -2) w vectors nohead lc rgb "#808080" lw 10 not
}
