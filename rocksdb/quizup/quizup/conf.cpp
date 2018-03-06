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
      ("encoded_params", po::value<string>()->default_value(Get("encoded_params")))
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

    string v = vm["encoded_params"].as<string>();
    Cons::P(v);
    exit(0);
    // TODO
    //string v = vm["encoded_params"].as<string>();
    //vm.

    __EditYaml<bool>("cache_filter_index_at_all_levels", vm);
    __EditYaml<bool>("monitor_temp", vm);
    __EditYaml<bool>("migrate_sstables", vm);
    __EditYaml<bool>("organize_L0_sstables", vm);
    __EditYaml<string>("db_path", vm);
    __EditYaml<double>("workload_start_from", vm);
    __EditYaml<double>("workload_stop_at", vm);
    __EditYaml<int>("simulation_time_dur_in_sec", vm);
    __EditYaml<int>("record_size", vm);
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

  const string GetStr(const std::string& k) {
    return _yaml_root[k].as<string>();
  }

  string GetDir(const std::string& k) {
    return boost::regex_replace(_yaml_root[k].as<string>(), boost::regex("~"), Util::HomeDir());
  }
};
