import socket


_job_id = None
def JobId():
	global _job_id
	if _job_id is not None:
		return _job_id

	hn = socket.gethostname()
	t = hn.split("-")
	_job_id = t[3] + "-" + t[4]
	return _job_id


# Convert format for gnuplot
#   from: 2016-09-20 15:40:34,382
#         01234567890123456789012
#   to:   160920-154034.382
def ShortDateTime(dt):
	return dt[2:4] + dt[5:7] + dt[8:10] \
				+ "-" + dt[11:13] + dt[14:16] + dt[17:19] \
				+ "." + dt[20:]
