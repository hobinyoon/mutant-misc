#include <limits.h>
#include <unistd.h>

#include <iostream>
#include <string>

#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/join.hpp>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <boost/regex.hpp>

#include "conf.h"
#include "cons.h"
#include "util.h"


using namespace std;

namespace Conf {
  YAML::Node _yaml_root;

  void _LoadYaml() {
    string fn = str(boost::format("%s/config.yaml") % boost::filesystem::path(__FILE__).parent_path().string());
    _yaml_root = YAML::LoadFile("config.yaml");
  }

  namespace po = boost::program_options;

  template<class T>
  void __EditYaml(const string& key, po::variables_map& vm) {
    if (vm.count(key) != 1)
      return;
    T v = vm[key].as<T>();
    static const auto sep = boost::is_any_of(".");
    vector<string> tokens;
    boost::split(tokens, key, sep, boost::token_compress_on);
    // Had to use a pointer to traverse the tree. Otherwise, the tree gets
    // messed up.
    YAML::Node* n = &_yaml_root;
    for (string t: tokens) {
      YAML::Node n1 = (*n)[t];
      n = &n1;
    }
    *n = v;
    //Cons::P(Desc());
  }

  void _ParseArgs(int argc, char* argv[]) {
    po::options_description od("Allowed options");
    od.add_options()
      ("help", "show help message")

      ("cache_filter_index_at_all_levels", po::value<bool>()->default_value(Get("cache_filter_index_at_all_levels").as<bool>()))
      ("monitor_temp", po::value<bool>()->default_value(Get("monitor_temp").as<bool>()))
      ("migrate_sstables", po::value<bool>()->default_value(Get("migrate_sstables").as<bool>()))
      ("sst_ott", po::value<double>()->default_value(Get("sst_ott").as<double>()))
      ("organize_L0_sstables", po::value<bool>()->default_value(Get("organize_L0_sstables").as<bool>()))
      ("db_path", po::value<string>()->default_value(GetStr("db_path")))
      ("slow_dev1_path", po::value<string>()->default_value(GetStr("slow_dev1_path")))
      ("slow_dev2_path", po::value<string>()->default_value(GetStr("slow_dev2_path")))
      ("slow_dev3_path", po::value<string>()->default_value(GetStr("slow_dev3_path")))
      ("workload_start_from", po::value<double>()->default_value(Get("workload_start_from").as<double>()))
      ("workload_stop_at", po::value<double>()->default_value(Get("workload_stop_at").as<double>()))
      ("simulation_time_dur_in_sec", po::value<int>()->default_value(Get("simulation_time_dur_in_sec").as<int>()))
      ("record_size", po::value<int>()->default_value(Get("record_size").as<int>()))
      ("121x_speed_replay", po::value<bool>()->default_value(Get("121x_speed_replay").as<bool>()))
      ("pid_params", po::value<string>()->default_value(Get("pid_params").as<string>()))

      ("sla_admin_type", po::value<string>()->default_value(Get("sla_admin_type").as<string>()))
      ("sla_observed_value_hist_q_size", po::value<int>()->default_value(Get("sla_observed_value_hist_q_size").as<int>()))
      ("sst_ott_adj_ranges", po::value<string>()->default_value(GetStr("sst_ott_adj_ranges")))
      ("slow_dev", po::value<string>()->default_value(GetStr("slow_dev")))
      ("slow_dev_target_r_iops", po::value<double>()->default_value(Get("slow_dev_target_r_iops").as<double>()))
      ("sst_ott_adj_cooldown_ms", po::value<int>()->default_value(Get("sst_ott_adj_cooldown_ms").as<int>()))

      ("extra_reads", po::value<bool>()->default_value(Get("extra_reads").as<bool>()))
      ("xr_queue_size", po::value<int>()->default_value(Get("xr_queue_size").as<int>()))
      ("xr_iops", po::value<double>()->default_value(Get("xr_iops").as<double>()))
      ("xr_gets_per_key", po::value<int>()->default_value(Get("xr_gets_per_key").as<int>()))
      ;

    po::variables_map vm;
    po::store(po::command_line_parser(argc, argv).options(od).run(), vm);
    po::notify(vm);

    if (vm.count("help") > 0) {
      // well... this doesn't show boolean as string.
      cout << std::boolalpha;
      cout << od << "\n";
      exit(0);
    }

    __EditYaml<bool>("cache_filter_index_at_all_levels", vm);
    __EditYaml<bool>("monitor_temp", vm);
    __EditYaml<bool>("migrate_sstables", vm);
    __EditYaml<double>("sst_ott", vm);
    __EditYaml<bool>("organize_L0_sstables", vm);
    __EditYaml<string>("db_path", vm);
    __EditYaml<string>("slow_dev1_path", vm);
    __EditYaml<string>("slow_dev2_path", vm);
    __EditYaml<string>("slow_dev3_path", vm);
    __EditYaml<double>("workload_start_from", vm);
    __EditYaml<double>("workload_stop_at", vm);
    __EditYaml<int>("simulation_time_dur_in_sec", vm);
    __EditYaml<int>("record_size", vm);
    __EditYaml<bool>("121x_speed_replay", vm);
    __EditYaml<string>("pid_params", vm);

    __EditYaml<string>("sla_admin_type", vm);
    __EditYaml<int>("sla_observed_value_hist_q_size", vm);
    __EditYaml<string>("sst_ott_adj_ranges", vm);
    __EditYaml<string>("slow_dev", vm);
    __EditYaml<double>("slow_dev_target_r_iops", vm);
    __EditYaml<int>("sst_ott_adj_cooldown_ms", vm);

    __EditYaml<bool>("extra_reads", vm);
    __EditYaml<int>("xr_queue_size", vm);
    __EditYaml<double>("xr_iops", vm);
    __EditYaml<int>("xr_gets_per_key", vm);
  }

  void Init(int argc, char* argv[]) {
    Cons::MT _("Initializing configurations ...", false);
    _LoadYaml();
    _ParseArgs(argc, argv);
    Cons::P(Desc());
  }

  string Desc() {
    YAML::Emitter emitter;
    emitter << _yaml_root;
    if (! emitter.good())
      THROW("Unexpected");
    return emitter.c_str();
  }

  YAML::Node Get(const std::string& k) {
    return _yaml_root[k];
  }

  string GetStr(const std::string& k) {
    return _yaml_root[k].as<string>();
  }

  string GetDir(const std::string& k) {
    return boost::regex_replace(_yaml_root[k].as<string>(), boost::regex("~"), Util::HomeDir());
  }
};
