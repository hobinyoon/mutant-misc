#!/usr/bin/env python

import datetime
import os
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

# Assume the workload is to a single database node.


def main(argv):
	Read()
	Write()


_ops = None

def Read():
	# Read the raw, anonymized data
	fn_in = "%s/work/quizup/86400-sec-redis-ephemeral-cmds.anonymized.log" \
			% os.path.expanduser("~")
	num_lines = 119874265
	# $ time wc -l 86400-sec-redis-ephemeral-cmds.anonymized.log
	#   119,874,265
	#   real 0m11.896s
	with Cons.MT("Reading %s" % fn_in):
		global _ops
		_ops = []
		with open(fn_in) as fo:
			i = 0
			#for line in fo.readlines():
			for line in fo:
				i += 1
				#Cons.P(line)
				op = Op(line)
				if op.cmd_type is None:
					continue
				_ops.append(op)
				if i % 10000 == 0:
					Cons.ClearLine()
					Cons.Pnnl("%d OPs read (%.2f%%), %d kept" % (i, 100.0 * i / num_lines, len(_ops)))
				# Useful for testing
				#if i >= 100000:
				#	break
			Cons.ClearLine()
			Cons.P("%d OPs read (%.2f%%), %d kept" % (i, 100.0 * i / num_lines, len(_ops)))


# Write in compact format
def Write():
	fn_out = "%s/work/quizup/86400-sec-redis-ephemeral-cmds.anonymized.compact.log" \
			% os.path.expanduser("~")
	with Cons.MT("Writing %s" % fn_out):
		with open(fn_out, "w") as fo:
			i = 0
			for op in _ops:
				i += 1
				fo.write("%s %s %s\n" % (op.ts, op.cmd, " ".join(op.key)))
				if i % 10000 == 0:
					Cons.ClearLine()
					Cons.Pnnl("Wrote %d OPs (%.2f%%)" % (i, 100.0 * i / len(_ops)))
		Cons.ClearLine()
		Cons.P("Wrote %d OPs (%.2f%%). File size %d" % (i, 100.0 * i / len(_ops), os.path.getsize(fn_out)))


class Op:
	def __init__(self, line):
		#Cons.P(line)
		# 1425006807.143991 [0 10.231.168.169:35587] "GET" "cabddac59895dee92bcdf9d5f8c99291a84c3541"
		#                 0  1                     2     3                                          4
		t = line.split()
		self.ts = t[0]
		self.cmd = t[3][1:-1]
		#Cons.P(cmd)
		self.cmd_type = None
		self.key = []

		# 1425006807.593476 [0 10.11.169.168:45560] "SET" "485e76a215b8535e2b952497c5a88b604e3cc760" "AAAA
		if self.cmd == "SET":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		# 1425006807.192817 [0 10.147.15.92:36323] "HINCRBY" "5c2df9a0902ad0bda092aeb4118a45e1c03f8579" "AAAAAAAAAAAAAAAAAAAAAAAAA" "AAA"
		elif self.cmd == "HINCRBY":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		# 1425006807.182856 [0 10.35.192.2:41998] "INCRBY" "9687044b2e6ec26ede3eebda90e6aea7aeb7a273" "AAA"
		elif self.cmd == "INCRBY":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		elif self.cmd == "LPUSH":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		elif self.cmd == "LTRIM":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		elif self.cmd == "RPUSH":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])
		elif self.cmd == "RESTORE":
			self.cmd_type = "w"
			self.key.append(t[4][1:-1])

		elif self.cmd == "DEL":
			self.cmd_type = "d"
			self.key.append(t[4][1:-1])
		elif self.cmd == "EXPIRE":
			self.cmd_type = "d"
			self.key.append(t[4][1:-1])
		elif self.cmd == "EXPIREAT":
			self.cmd_type = "d"
			self.key.append(t[4][1:-1])
		elif self.cmd == "LPOP":
			self.cmd_type = "d"
			self.key.append(t[4][1:-1])

		elif self.cmd == "GET":
			self.cmd_type = "r"
			self.key.append(t[4][1:-1])
		# 1425006807.183626 [0 10.140.169.154:40505] "DUMP" "7a90dbfdfff520003540a105b7b9ec0c86bb3059"
		elif self.cmd == "DUMP":
			self.cmd_type = "r"
			self.key.append(t[4][1:-1])
		# 1425006807.184042 [0 10.164.176.216:46133] "MGET" "bc18d051c2454c42b55b4d8783265f733b9a624c" "665b99dc8bfd7a79d03128477bc96e6535fc369f" "119cca158c0e41848df001a5585d1c9d1039c097"
		elif self.cmd == "MGET":
			self.cmd_type = "r"
			for k in t[4:]:
				self.key.append(k[1:-1])
		elif self.cmd == "LRANGE":
			self.cmd_type = "r"
			self.key.append(t[4][1:-1])
		elif self.cmd in ["EXEC", "EXISTS", "INFO", "LLEN", "MULTI", "PING", "REPLCONF"]:
			return
		else:
			RuntimeError("Unexpected %s" % line)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
