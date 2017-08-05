import os
import pprint
import sys

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

import Conf
import CsvFile


def Plot():
	with Cons.MT("Plotting ..."):
		stg_conf = {
				"latency_mutant_ls_es": "Local SSD + EBS SSD"
				, "latency_mutant_ls_st1": "Local SSD + EBS Mag"
				, "latency_mutant_ls_sc1": "Local SSD + EBS Mag Cold"
				}

		for stgconf, stgconf_label in stg_conf.iteritems():
			env = os.environ.copy()

			sst_mig_temp_thresholds = [int(k) for k, v in sorted(Conf.Manifest.Get(stgconf).iteritems())]
			#Cons.P(pprint.pformat(sst_mig_temp_thresholds))

			simulation_time_begins = [v for k, v in sorted(Conf.Manifest.Get(stgconf).iteritems())]
			#Cons.P(pprint.pformat(simulation_time_begins))

			for sst_mig_temp_th, simulation_time_begin in sorted(Conf.Manifest.Get(stgconf).iteritems()):
				sst_mig_temp_th = int(sst_mig_temp_th)
				#Cons.P("%3d %s" % (sst_mig_temp_th, simulation_time_begin))
				CsvFile.GenDataFileForGnuplot(simulation_time_begin)

			env["STG_CONF_LABEL"] = stgconf_label
			env["SST_MIG_TEMP_TH"] = " ".join(str(i) for i in sst_mig_temp_thresholds)
			env["SIMULATION_TIME_BEGIN"] = " ".join(i for i in simulation_time_begins)
			env["IN_FNS"] = " ".join(("%s/%s/dstat-data" % (Conf.GetDir("output_dir"), i)) for i in simulation_time_begins)

			fn_out = "%s/mutant-%s-iops-by-sstmigtempth.pdf" \
					% (Conf.GetDir("output_dir"), "-".join(stgconf.split("_")[2:]))
			env["OUT_FN"] = fn_out
			Util.RunSubp("gnuplot %s/iops-by-stgconf-by-sstmigtempth.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))
