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
	a = 10
	v = - math.pow(-v+1, a) + 1

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
