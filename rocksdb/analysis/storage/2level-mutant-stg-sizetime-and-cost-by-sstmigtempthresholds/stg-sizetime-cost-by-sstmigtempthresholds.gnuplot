# Tested with gnuplot 4.6 patchlevel 4

IN_FN = system("echo $IN_FN")
# Unmodified RocksDB cost in $/GB/Month
UR_COST_LOCAL_SSD = system("echo $UR_COST_LOCAL_SSD") + 0.0
UR_COST_EBS_SSD   = system("echo $UR_COST_EBS_SSD") + 0.0
UR_COST_EBS_MAG   = system("echo $UR_COST_EBS_MAG") + 0.0
# Unmodified RocksDB size*time in GB/Month
UR_SIZETIME       = system("echo $UR_SIZETIME") + 0.0
OUT_FN = system("echo $OUT_FN")

set print "-"
print sprintf("UR_COST_LOCAL_SSD=%f", UR_COST_LOCAL_SSD)
print sprintf("UR_COST_EBS_SSD  =%f", UR_COST_EBS_SSD  )
print sprintf("UR_COST_EBS_MAG  =%f", UR_COST_EBS_MAG  )
print sprintf("UR_SIZETIME      =%f", UR_SIZETIME      )
#print sprintf("OUT_FN=%s", OUT_FN)

set terminal pdfcairo enhanced size 2.5in, (2.3*0.85)in
set output OUT_FN

set border front lc rgb "#808080" back
set grid xtics ytics back lc rgb "#808080"
set xtics out nomirror tc rgb "black" ( \
  "2^{-12}" 2**(-12), \
  "2^{-8}" 2**(-8), \
  "2^{-4}" 2**(-4), \
  "2^{ 0}" 2**( 0), \
  "2^{ 4}" 2**( 4), \
  "2^{ 8}" 2**( 8) \
	)
set ytics nomirror tc rgb "black" ( \
	"50" 0.5, \
	"40" 0.4, \
	"30" 0.3, \
	"20" 0.2, \
	"10" 0.1, \
	 "0" 0.0 \
)
set tics back

set tmargin screen 0.915
set rmargin screen 0.87

set xlabel "SSTable OTT"
set ylabel "\nStorage cost (cent)" offset 0.5,0

X_MIN=(2**(-9)) / 1.5
X_MAX=(2**11) * 1.5

set xrange[X_MIN:X_MAX]
set yrange[0:0.5]

# Right label offset
o0 = 1.8
o1 = 3.6

# Baseline cost
if (1) {
	LW=7
	UR_COST_LOCAL_SSD=0.444267
	set arrow 1 from X_MIN, UR_COST_LOCAL_SSD to X_MAX*1.5, UR_COST_LOCAL_SSD nohead lt 0 lw LW lc rgb "black"
	set label 1 "RocksDB\n(Local SSD)" at X_MAX, UR_COST_LOCAL_SSD offset o0, 0 center rotate by 90 tc rgb "black"

	set arrow 2 from X_MIN, UR_COST_EBS_MAG to X_MAX*1.5, UR_COST_EBS_MAG nohead lt 0 lw LW lc rgb "black"
	set label 3 "RocksDB\n(EBS Mag)"   at X_MAX, UR_COST_EBS_MAG   offset o0, 0 center rotate by 90 tc rgb "black"
}

set logscale x

# Bar chart looks even better
TRANS=0.2

bar_width_ratio=1.4

# Legend
if (1) {
	set nokey
	x0 = X_MIN + 0.30 * (X_MAX-X_MIN)
	x1 = x0 + 0.30 * (X_MAX-X_MIN)
	y0 = 0.26
	y1 = y0 + 0.08
	y2 = y1 + 0.08

	set obj 1 rect from x0, y0 to x1, y1 fs solid TRANS border lw 2 fc rgb "blue" front
	set label 5 "EBS Mag" at x0, (y0+y1)/2.0 right offset -0.7, 0 tc rgb "blue"

	set obj 2 rect from x0, y1 to x1, y2 fs solid TRANS border lw 2 fc rgb "red" front
	set label 6 "Local SSD" at x0, (y1+y2)/2.0 right offset -0.7, 0 tc rgb "red"
}

plot \
IN_FN u ($1/bar_width_ratio):8  :($1/bar_width_ratio):($1*bar_width_ratio):8  :11 w boxxyerrorbars fs solid TRANS lw 2 lc rgb "red"  t "Local SSD", \
IN_FN u ($1/bar_width_ratio):(0):($1/bar_width_ratio):($1*bar_width_ratio):(0):8  w boxxyerrorbars fs solid TRANS lw 2 lc rgb "blue" t "EBS SSD"

# Storage size*time plot

set ylabel "Storage size {/Symbol \264} time\n(GB {/Symbol \264} Month)"

unset ytics
set ytics nomirror tc rgb "black" format "%.1f"

set yrange [0:1.0]

# Baseline size*time
if (1) {
	LW=7
	set arrow 1 from X_MIN, UR_SIZETIME to X_MAX*1.5, UR_SIZETIME nohead lt 0 lw LW lc rgb "black"
	set label 1 "RocksDB" at X_MAX, UR_SIZETIME offset o0, 0 center tc rgb "black"

	unset arrow 2
	unset label 2
	unset label 3
	unset label 4
	unset label 5
	unset label 6
}

# Manual legend plotting
if (0) {
	set nokey
	x0 = X_MIN + 0.5 * (X_MAX-X_MIN)
	x1 = x0 + 0.10 * (X_MAX-X_MIN)
	y0 = 0.30
	y1 = y0 + 0.1
	y2 = y1 + 0.1

	set obj 1 rect from x0, y0 to x1, y1 fs solid TRANS border lw 2 fc rgb "blue" front
	set label 3 "EBS SSD" at x0, (y0+y1)/2.0 right offset -0.7, 0 tc rgb "blue"

	set obj 2 rect from x0, y1 to x1, y2 fs solid TRANS border lw 2 fc rgb "red" front
	set label 4 "Local SSD" at x0, (y1+y2)/2.0 right offset -0.7, 0 tc rgb "red"
} else {
	unset obj 1
	unset label 3
	unset obj 2
	unset label 4
}

plot \
IN_FN u ($1/bar_width_ratio):3  :($1/bar_width_ratio):($1*bar_width_ratio):3  :6 w boxxyerrorbars fs solid TRANS lw 2 lc rgb "red"  t "Local SSD", \
IN_FN u ($1/bar_width_ratio):(0):($1/bar_width_ratio):($1*bar_width_ratio):(0):3 w boxxyerrorbars fs solid TRANS lw 2 lc rgb "blue" t "EBS SSD"

# boxxyerrorbars: x y xlow xhigh ylow yhigh
