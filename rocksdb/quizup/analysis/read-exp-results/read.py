#!/usr/bin/env python

import os
import pprint
import sys
import yaml

import ClientLogReader

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	dn = "%s/work/mutant/misc/rocksdb/log" % os.path.expanduser("~")
	fn = "%s/manifest.yaml" % dn

	doc = None
	with open(fn) as fo:
		doc = yaml.load(fo)
	#Cons.P(pprint.pformat(doc["new_exps"]))
	
	# {exp_desc: ClientLogReader()}
	expdesc_log = {}
	for simulation_time_begin in doc["New exps"]:
		log = ClientLogReader.ClientLogReader(simulation_time_begin)
		if log.options["exp_desc"] not in expdesc_log:
			expdesc_log[log.options["exp_desc"]] = []
		expdesc_log[log.options["exp_desc"]].append(log)
	
	for exp_desc, logs in sorted(expdesc_log.iteritems()):
		Cons.P("# Desc: %s" % exp_desc)
		fmt = "%17s %10s %7s %1s %4.0f" \
				" %1s %1s %1s %1s %5s %5s %5s %17s"
		Cons.P(Util.BuildHeader(fmt, "simulation_time_begin" \
				" fast_dev_path" \
				" slow_dev1_path" \
				" init_db_to_90p_loaded" \
				" memory_limit_in_mb" \
				\
				" mutant_enabled(for_old_exps)" \
				" cache_filter_index_at_all_levels" \
				" monitor_temp migrate_sstables" \
				" workload_start_from" \
				" workload_stop_at" \
				" simulation_time_dur_in_sec" \
				" sst_migration_temperature_threshold" \
				))
		for l in logs:
			Cons.P(fmt % (l.simulation_time_begin
				, l.options["fast_dev_path"]
				, l.options["slow_dev1_path"]
				, V_bool(l.options, "init_db_to_90p_loaded")
				, float(l.options["memory_limit_in_mb"])
				, V_bool(l.options, "mutant_enabled")
				, V_bool(l.options, "cache_filter_index_at_all_levels")
				, V_bool(l.options, "monitor_temp")
				, V_bool(l.options, "migrate_sstables")
				, l.options["workload_start_from"]
				, l.options["workload_stop_at"]
				, l.options["simulation_time_dur_in_sec"]
				, l.options["sst_migration_temperature_threshold"]
				))
		Cons.P("")


def V_bool(d, k):
	if k not in d:
		return "-"
	if d[k].lower() == "true":
		return "1"
	else:
		return "0"


if __name__ == "__main__":
	sys.exit(main(sys.argv))
