import os
import re
import sys
import zipfile

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Util0

_lines = None
def Get():
	global _lines
	if _lines is not None:
		return _lines

	with Cons.MT("Reading Cassandra log ..."):
		_lines = _ReadStoredLog()
		if _lines is not None:
			return _lines

		_lines = _ReadAndCacheCassLog()
		return _lines


def _ReadStoredLog():
	if Conf.ExpStartTime() is None:
		return None

	dn = "%s/work/mutant/misc/logs/cassandra" % os.path.expanduser("~")
	fn = "%s/system-%s" % (dn, Conf.ExpStartTime())
	if not os.path.isfile(fn):
		# If there is a 7z file, uncompress it
		fn_7z = "%s.7z" % fn
		if os.path.isfile(fn_7z):
			with Cons.MT("Found a 7z file. Uncompressing"):
				Util.RunSubp("7z e -o%s %s" % (dn, fn_7z))
		else:
			return None

	with Cons.MT("Reading the stored Cassandra Mutant log file %s" % fn, print_time=False):
		lines = []
		with open(fn) as fo:
			for line in fo.readlines():
				lines.append(line.strip())
				# Stop after reading n lines for testing
				if 0 < Conf.MaxCassLogLines():
					if Conf.MaxCassLogLines() < len(lines):
						break
		#Cons.P(len(lines))

		return lines


# ResetMon is not always there. Use the provided exp_start_time, which is the
# latest dstat start time on the client node.
#
# Check until you see two datetimes that cross the given exp_start_time
def _ReadAndCacheCassLogUntilDtCrossesStNotTested():
	with Cons.MT("Reading Cassandra log ..."):
		# Note: s0 only for now.
		dn = "%s/work/mutant/log/%s/s0/cassandra" % (os.path.expanduser("~"), Util0.JobId())

		# Start from system.log and keep reading system.log.n.zip where n >= 1,
		# until you find two datetimes that cross the given exp start time
		st = Conf.ExpStartTime()
		ft = Conf.ExpFinishTime()
		dt_prev = None
		dt_crossed_st = False

		# WARN  [main] 2016-09-20 02:20:39,250 MemSsTableAccessMon.java:115 - Mutant: ...
		pattern = re.compile(r".+" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" .+")

		fn = "%s/system.log" % dn
		lines = []
		Cons.P("fn=%s" % fn)
		with open(fn) as fo:
			for line in fo.readlines():
				line = line.strip()
				mo = pattern.match(line)
				if mo is None:
					raise RuntimeError("Unexpected line=[%s]" % line)
				dt = Util0.ShortDateTime(mo.group("datetime"))
				if (st <= dt) and (dt <= ft):
					lines.append(line)
				if ft < dt:
					break
				if not dt_crossed_st:
					if (dt_prev is not None) and (dt_prev < st) and (st < dt):
						dt_crossed_st = True
				dt_prev = dt

		# Keep reading zipped files like system.log.1.zip, until ResetMon is found
		i = 1
		while dt_crossed_st == False:
			fn = "%s/system.log.%d.zip" % (dn, i)
			Cons.P("dt haven't crossed st yet. Reading more logs from file %s ..." % fn)
			lines1 = []
			with zipfile.ZipFile(fn, "r") as z:
				dt_prev = None
				for fn1 in z.namelist():
					#Cons.P(fn1)
					for line in z.read(fn1).split("\n"):
						line = line.strip()
						#Cons.P(line)
						mo = pattern.match(line)
						if mo is None:
							raise RuntimeError("Unexpected line=[%s]" % line)
						dt = Util0.ShortDateTime(mo.group("datetime"))
						if (st <= dt) and (dt <= ft):
							lines.append(line)
						if ft < dt:
							break
						if not dt_crossed_st:
							if (dt_prev is not None) and (dt_prev < st) and (st < dt):
								dt_crossed_st = True
						dt_prev = dt
						lines1.append(line)
			if len(lines1) != 0:
				lines1.extend(lines)
				lines = list(lines1)
				del lines1[:]
			i += 1

		fn = "%s/work/mutant/misc/logs/cassandra/system-%s" \
				% (os.path.expanduser("~"), Conf.ExpStartTime())
		with open(fn, "w") as fo:
			for line in lines:
				fo.write("%s\n" % line)
		Cons.P("Created a Cassandra log file %s %d" % (fn, os.path.getsize(fn)))

		return lines


# Read till the end of the log file to get sstable sizes and timestamp ranges
# that are available when first SSTable open-normal. The plot will be trimmed
# by an end time.
def _ReadAndCacheCassLog():
	with Cons.MT("Reading Cassandra log ..."):
		lines = []
		found_reset = False
		lines1 = []

		# WARN  [main] 2016-09-20 02:20:39,250 MemSsTableAccessMon.java:115 - Mutant: ResetMon
		pattern = re.compile(r"WARN  \[(main|MigrationStage:\d+)\]" \
				" (?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)" \
				" MemSsTableAccessMon.java:\d+ -" \
				" Mutant: (?P<event>ResetMon)")

		# Note: s0 only for now.
		dn = "%s/work/mutant/log/%s/s0/cassandra" % (os.path.expanduser("~"), Util0.JobId())
		fn = "%s/system.log" % dn
		Cons.P("fn=%s" % fn)
		with open(fn) as fo:
			for line in fo.readlines():
				line = line.strip()
				mo = pattern.match(line)
				if mo is not None:
					found_reset = True
					Conf.SetExpStartTime(Util0.ShortDateTime(mo.group("datetime")))
					del lines[:]
				lines.append(line)

		# Keep reading zipped files like system.log.1.zip, until ResetMon is found
		i = 1
		while found_reset == False:
			fn = "%s/system.log.%d.zip" % (dn, i)
			Cons.P("ResetMon not found. Reading more from file %s ..." % fn)
			with zipfile.ZipFile(fn, "r") as z:
				for fn1 in z.namelist():
					#Cons.P(fn1)
					for line in z.read(fn1).split("\n"):
						line = line.strip()
						#Cons.P(line)
						mo = pattern.match(line)
						if mo is not None:
							found_reset = True
							Conf.SetExpStartTime(Util0.ShortDateTime(mo.group("datetime")))
							del lines1[:]
						lines1.append(line)
			if len(lines1) != 0:
				lines1.extend(lines)
				lines = list(lines1)
				del lines1[:]
			i += 1

		fn = "%s/work/mutant/misc/logs/cassandra/system-%s" \
				% (os.path.expanduser("~"), Conf.ExpStartTime())
		with open(fn, "w") as fo:
			for line in lines:
				fo.write("%s\n" % line)
		Cons.P("Created a Cassandra log file %s %d" % (fn, os.path.getsize(fn)))

		return lines
