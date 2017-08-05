import datetime
import json
import os
import pprint
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import Util0


_cl = None
def Get():
	global _cl
	if _cl is not None:
		return _cl

	with Cons.MT("Reading Cassandra compaction log ..."):
		_cl = CompactionLog()
		return _cl


def HowCreated(sst_gen):
	cl = Get()
	return cl.HowCreated(sst_gen)


class CompactionLog:
	def __init__(self):
		if Conf.ExpStartTime() is None:
			raise RuntimeError("Unexpected")
		dn = "%s/work/mutant/misc/logs/cassandra" % os.path.expanduser("~")
		self.fn_compaction_log = "%s/compaction-%s" % (dn, Conf.ExpStartTime())

		# If not exist and there is a 7z file, uncompress it
		if not os.path.isfile(self.fn_compaction_log):
			fn_7z = "%s.7z" % self.fn_compaction_log
			if os.path.isfile(fn_7z):
				with Cons.MT("Found a 7z file. Uncompressing"):
					Util.RunSubp("7z e -o%s %s" % (dn, fn_7z))

		# If still not exist, Copy the current compaction log file
		if not os.path.isfile(self.fn_compaction_log):
			dn1 = "%s/work/mutant/log/%s/s0/cassandra" % (os.path.expanduser("~"), Util0.JobId())
			Util.RunSubp("cp %s/compaction.log %s" \
					% (dn1, self.fn_compaction_log))

		with Cons.MT("Reading compaction log %s" % self.fn_compaction_log, print_time=False):
			self.Read()

	def Read(self):
		# {ssd_id: how_created}
		self.sstid_howcreated = {}

		self.proceed_with_pending_compactions = None

		# Read the log
		with open(self.fn_compaction_log) as fo:
			for line in fo.readlines():
				# Looks like they are in json format
				#Cons.P(line)
				e = json.loads(line)
				#Cons.P(pprint.pformat(e))

				if (e["keyspace"] != "ycsb") or (e["table"] != "usertable"):
					raise RuntimeError("Unexpected\n%s" % pprint.pformat(e))

				if e["type"] == "enable":
					continue
				elif e["type"] == "flush":
					for t in e["tables"]:
						sst_gen = int(t["table"]["generation"])
						if sst_gen in self.sstid_howcreated:
							raise RuntimeError("Unexpected")
						self.sstid_howcreated[sst_gen] = CompactionLog._HowCreated("flushed")
					continue
				elif e["type"] == "pending":
					if int(e["pending"]) <= 2:
						continue
					# Prompt for pending compactions
					if self.proceed_with_pending_compactions is None:
						Cons.P("There are pending compactions, which indicate the server is overloaded.")
						Cons.P(pprint.pformat(e), ind=2)
						Cons.Pnnl("Would you like to proceed ")
						self.proceed_with_pending_compactions = raw_input("(Y/N)? ")
						if self.proceed_with_pending_compactions.lower() != "y":
							sys.exit(0)
						else:
							continue
				elif e["type"] == "compaction":
					# {u'end': u'1474839005076',
					#  u'input': [{u'strategyId': u'1',
					#              u'table': {u'details': {u'level': 0,
					#                                      u'max_token': u'9223342625191452161',
					#                                      u'min_token': u'-9222223702120529941'},
					#                         u'generation': 1,
					#                         u'size': 14061373,
					#                         u'version': u'mc'}},
					#             {u'strategyId': u'1',
					#              u'table': {u'details': {u'level': 0,
					#                                      u'max_token': u'9222611853699094103',
					#                                      u'min_token': u'-9221429980877775654'},
					#                         u'generation': 2,
					#                         u'size': 14050279,
					#                         u'version': u'mc'}}],
					#  u'keyspace': u'ycsb',
					#  u'output': [{u'strategyId': u'1',
					#               u'table': {u'details': {u'level': 0,
					#                                       u'max_token': u'9223342625191452161',
					#                                       u'min_token': u'-9222223702120529941'},
					#                          u'generation': 3,
					#                          u'size': 28117799,
					#                          u'version': u'mc'}}],
					#  u'start': u'1474839003093',
					#  u'table': u'usertable',
					#  u'time': 1474839005076,
					#  u'type': u'compaction'}
					#
					# time and end seem to have the same value
					time = int(e["time"])
					start = int(e["start"])
					end = int(e["end"])

					# Set experiment end time: last compaction event + the duration of
					# the compaction. Or, the last seen Mutant event timestamp can be
					# used too, depending on whether you want a stabilized snapshot of
					# SSTables or a snapshot while data is being added.
					#
					#Conf.SetExpFinishTime(datetime.datetime.fromtimestamp(int(end + (end - start)) / 1000.0)
					#		.strftime("%y%m%d-%H%M%S.%f")
					#		# Trim the last 3 digits
					#		[:-3])

					input_tables = []
					output_tables = []
					for e1 in e["input"]:
						if e1["strategyId"] != "1":
							raise RuntimeError("Unexpected\n%s" % pprint.pformat(e))
						e1["table"]["details"]["level"]
						e1["table"]["details"]["max_token"]
						e1["table"]["details"]["min_token"]
						input_tables.append(int(e1["table"]["generation"]))
						e1["table"]["size"]

					for e1 in e["output"]:
						if e1["strategyId"] != "1":
							raise RuntimeError("Unexpected\n%s" % pprint.pformat(e))
						e1["table"]["details"]["level"]
						e1["table"]["details"]["max_token"]
						e1["table"]["details"]["min_token"]
						sst_gen = int(e1["table"]["generation"])
						e1["table"]["size"]

						if sst_gen in self.sstid_howcreated:
							raise RuntimeError("Unexpected")
						self.sstid_howcreated[sst_gen] = CompactionLog._HowCreated("compacted", input_tables)

					#Cons.P("\n%s\n%s\n%s" % (time, start, end))
					continue
				else:
					raise RuntimeError("Unexpected\n%s" % pprint.pformat(e))

	def HowCreated(self, sst_gen):
		if sst_gen not in self.sstid_howcreated:
			return ""
		return self.sstid_howcreated[sst_gen]

	class _HowCreated:
		def __init__(self, how, input_tables=None):
			self.how = how
			self.input_tables = input_tables

		def __repr__(self):
			s = self.how
			if self.input_tables is not None:
				s += ("(%s)" % ",".join(str(i) for i in self.input_tables))
			return s
