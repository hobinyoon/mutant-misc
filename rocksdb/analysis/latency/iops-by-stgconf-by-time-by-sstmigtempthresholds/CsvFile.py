import csv
import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import SimTime


_header_idx = None
_body_rows = None


# Not thread-safe. Depends on the global variables. It's okay for now.
def GenDataFileForGnuplot(dt):
	SimTime.Init(dt)

	dn = "%s/%s" % (Conf.GetDir("output_dir"), dt)
	Util.MkDirs(dn)
	fn = "%s/dstat-data" % dn
	if os.path.isfile(fn):
		return fn

	with Cons.MT("Generating data file for plot ..."):
		global _header_idx
		global _body_rows
		_header_idx = None
		_body_rows = None

		_Parse(dt)

		fmt = "%9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f" \
				" %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f" \
				" %8.0f %8.0f %8.0f %8.0f" \
				" %3.0f %3.0f" \
				" %3.0f %3.0f %11s" \
				" %3.1f %6.2f %3.1f %6.2f %6.2f %6.3f"
		header = Util.BuildHeader(fmt, " ".join(k for k, v in sorted(_header_idx.iteritems())))
		with open(fn, "w") as fo:
			i = 0
			for r in _body_rows:
				if i % 50 == 0:
					fo.write("%s\n" % header)
				i += 1
				#Cons.P(fmt % tuple(r.Prepared()))
				fo.write((fmt + "\n") % tuple(r.Prepared()))
		Cons.P("Created %s %d" % (fn, os.path.getsize(fn)))
		return fn


class BodyRow:
	def __init__(self, r):
		self.raw_row = r

	def NumCols(self):
		return len(self.raw_row)

	# Sort the data in the header order and convert strings to numbers
	def PrepareData(self):
		simulation_time_begin_year = SimTime.SimulationTimeBegin().strftime("%y")

		self.row = []
		for h, i in sorted(_header_idx.iteritems()):
			if h.startswith("dsk/xvd") \
					or h.startswith("io/xvd") \
					or h.startswith("total_cpu_usage:"):
						self.row.append(float(self.raw_row[i]))
			elif h.startswith("system:time"):
				# It doesn't have year. Use simulation_time_begin_year.
				# 27-12 15:34:18
				# 01234567890123
				simulation_time = datetime.datetime.strptime((simulation_time_begin_year + self.raw_row[i]), "%y%d-%m %H:%M:%S")
				self.row.append(SimTime.ToSimulatedTime(simulation_time).strftime("%m%d-%H%M%S"))
			elif h.startswith("memory_usage:") \
					or h.startswith("net/total:") \
					or h.startswith("system:"):
				self.row.append(float(self.raw_row[i]) / 1024.0)
			else:
				self.row.append(self.raw_row[i])


	def Prepared(self):
		return self.row


def _Parse(dt):
	dn = "%s/dstat" % Conf.GetDir("log_dir")
	fn = "%s/%s.csv" % (dn, dt)
	if not os.path.isfile(fn):
		fn_7z = "%s.7z" % fn
		if not os.path.isfile(fn_7z):
			raise RuntimeError("Unexpected")
		Util.RunSubp("cd %s && 7z e %s" % (dn, fn_7z))
	if not os.path.isfile(fn):
		raise RuntimeError("Unexpected")

	with Cons.MT("Parsing %s ..." % fn):
		header_rows = []
		global _body_rows
		_body_rows = []
		with open(fn, "rb") as f:
			header_detected = False
			reader = csv.reader(f)
			for row in reader:
				if (len(row) > 0) and (row[0] in ["system", "time"]):
					header_rows.append(row)
					header_detected = True
				elif header_detected:
					_body_rows.append(BodyRow(row))
			#Cons.P(pprint.pformat(header_rows))
		
		# Make sure the rows are all the same size
		num_cols = None
		for r in header_rows:
			if num_cols is None:
				num_cols = len(r)
			else:
				if num_cols != len(r):
					raise RuntimeError("Unexpected")

		for r in _body_rows:
			if num_cols != r.NumCols():
				raise RuntimeError("Unexpected")
		
		# Get column headers
		global _header_idx
		_header_idx = {}
		header_rows_0_prev = None
		for i in range(num_cols):
			if len(header_rows[0][i]) > 0:
				#Cons.P("%s, %s" % (header_rows[0][i], header_rows[1][i]))
				_header_idx["%s:%s" % (header_rows[0][i].replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
				header_rows_0_prev = header_rows[0][i].replace(" ", "_")
			else:
				#Cons.P("%s, %s" % (header_rows_0_prev, header_rows[1][i]))
				_header_idx["%s:%s" % (header_rows_0_prev.replace(" ", "_"), header_rows[1][i].replace(" ", "_"))] = i
		#Cons.P(pprint.pformat(_header_idx))

		# Sort the data in the header order and convert strings to numbers
		for b in _body_rows:
			b.PrepareData()
