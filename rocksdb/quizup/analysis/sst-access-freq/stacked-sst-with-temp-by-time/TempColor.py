import math


def Get(v):
	# Curve the heat mapping
	#
	# With a circle with the center at (1 + a, 0 - a) and passes (0,
	# 0) and (1, 1)
	#a = 0
	#v = math.sqrt(2*a*a + 2*a + 1 - (v-1-a)*(v-1-a)) - a
	#
	# With a reciprocal function. This is the best!
	#v = 1 - a/(v+b) + b
	#
	# With an exponential function. You can play with the exponent.
	if False:
		a = 10
		v = - math.pow(-v+1, a) + 1

	# Polynomial regression using these. Didn't work. I suspect the precision is not good enough.
	#   1           1
	#   0.1         0.8
	#   0.01        0.6
	#   0.001       0.4
	#   0.0001      0.2
	#   0.00001     0
	# y = -250189.9326 x4 + 278211.175 x3 - 28328.99578 x2 + 308.7842066 x - 3.05859847*10-2
	#v = -250189.9326 * math.pow(v, 4) \
	#		+ 278211.175 * math.pow(v, 3) \
	#		- 28328.99578 * math.pow(v, 2) \
	#		+ 308.7842066 * v \
	#		- 0.0305859847

	# (-5, 0]
	v = math.log10(v) / 3.0 + 1
	if v < 0:
		v = 0

	# 1    red    #FF0000 16711680
	# 0.5  white  #FFFFFF 16777215
	# 0    blue   #0000FF 255
	if v < 0.5:
		return int(v / 0.5 * 255.9999999) * 256 * 256 + int(v / 0.5 * 255.9999999) * 256 + 255
	return 255 * 256 * 256 + int((1.0 - v) / 0.5 * 255.9999999) * 256 + int((1.0 - v) / 0.5 * 255.9999999)

	# 1    red    #FF0000 16711680
	# 0.75 yellow #FFFF00 16776960
	# 0.5  green  #00FF00 65280
	# 0.25 cyan   #00FFFF 65535
	# 0    blue   #0000FF 255
	#
	#if v < 0.25:
	#	return 255 + int((v / 0.25) * 255.9999999) * 256
	#if v < 0.5:
	#	return 65280 + int((1 - (v - 0.25) / 0.25) * 255.9999999)
	#if v < 0.75:
	#	return 65280 + int((v - 0.50) / 0.25 * 255.9999999) * 256 * 256
	#return 16711680 + int((1 - (v - 0.75) / 0.25) * 255.9999999) * 256

	#	if v < 0.25:
	#		return 16711680 + int((v / 0.25) * 255.9999999) * 256
	#	if v < 0.5:
	#		return 65280 + int((1 - (v - 0.25) / 0.25) * 255.9999999) * 256 * 256
	#	if v < 0.75:
	#		return 65280 + int((v - 0.50) / 0.25 * 255.9999999)
	#	return 255 + int((1 - (v - 0.75) / 0.25) * 255.9999999) * 256
