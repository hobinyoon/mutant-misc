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
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/filter/zlib.hpp>

#include <jsoncpp/json/json.h>
#include <jsoncpp/json/reader.h>
#include <jsoncpp/json/writer.h>
#include <jsoncpp/json/value.h>

#include "conf.h"
#include "cons.h"
#include "util.h"


using namespace std;


// https://stackoverflow.com/questions/180947/base64-decode-snippet-in-c
namespace Base64 {
  static const std::string base64_chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/";

  static inline bool is_base64(unsigned char c) {
    return (isalnum(c) || (c == '+') || (c == '/'));
  }

  std::string Encode(unsigned char const* bytes_to_encode, unsigned int in_len) {
    std::string ret;
    int i = 0;
    int j = 0;
    unsigned char char_array_3[3];
    unsigned char char_array_4[4];

    while (in_len--) {
      char_array_3[i++] = *(bytes_to_encode++);
      if (i == 3) {
        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
        char_array_4[3] = char_array_3[2] & 0x3f;

        for(i = 0; (i <4) ; i++)
          ret += base64_chars[char_array_4[i]];
        i = 0;
      }
    }

    if (i)
    {
      for(j = i; j < 3; j++)
        char_array_3[j] = '\0';

      char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
      char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
      char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
      char_array_4[3] = char_array_3[2] & 0x3f;

      for (j = 0; (j < i + 1); j++)
        ret += base64_chars[char_array_4[j]];

      while((i++ < 3))
        ret += '=';

    }

    return ret;
  }

  std::string Decode(std::string const& encoded_string) {
    int in_len = encoded_string.size();
    int i = 0;
    int j = 0;
    int in_ = 0;
    unsigned char char_array_4[4], char_array_3[3];
    std::string ret;

    while (in_len-- && ( encoded_string[in_] != '=') && is_base64(encoded_string[in_])) {
      char_array_4[i++] = encoded_string[in_]; in_++;
      if (i ==4) {
        for (i = 0; i <4; i++)
          char_array_4[i] = base64_chars.find(char_array_4[i]);

        char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);
        char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);
        char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

        for (i = 0; (i < 3); i++)
          ret += char_array_3[i];
        i = 0;
      }
    }

    if (i) {
      for (j = i; j <4; j++)
        char_array_4[j] = 0;

      for (j = 0; j <4; j++)
        char_array_4[j] = base64_chars.find(char_array_4[j]);

      char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);
      char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);
      char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

      for (j = 0; (j < i - 1); j++) ret += char_array_3[j];
    }

    return ret;
  }
};


bool _GetBool(const Json::Value& j, const std::string& key) {
  std::string s = j.get(key, "").asString();
  std::transform(s.begin(), s.end(), s.begin(), ::tolower);
  return (s == "true");
}


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
      ("encoded_params", po::value<string>())
      //("encoded_params", po::value<string>()->default_value(Get("encoded_params")))
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

    // Base64 decode
    // // TODO
    std::string mo2 = Base64::Decode(v);

    // Unzip
    //   https://stackoverflow.com/questions/27529570/simple-zlib-c-string-compression-and-decompression
    std::string mo3;
    {
      boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
      in.push(boost::iostreams::zlib_decompressor());
      std::stringstream ss1;
      ss1 << mo2;
      in.push(ss1);
      std::stringstream ss2;
      boost::iostreams::copy(in, ss2);
      mo3 = ss2.str();
      //TRACE << boost::format("mo3: %s\n") % mo3;
    }

    // Parse json
    Json::Value json_root;
    {
      Json::Reader reader;
      if (! reader.parse(mo3, json_root)) {
        std::cout << "Failed to parse" << reader.getFormattedErrorMessages();
        exit(1);
      }
      std::cout << boost::format("Mutant options: %s\n") % json_root;
    }

    Cons::P(json_root.toStyledString());

    // TODO

    // // If non-zero, we perform bigger reads when doing compaction. If you're running RocksDB on spinning disks, you should set this to at
    // // least 2MB.  That way RocksDB's compaction is doing sequential instead of random reads.
    // // When non-zero, we also force new_table_reader_for_compaction_inputs to true.
    // options->compaction_readahead_size = 2 * 1024 * 1024;

    // for (auto i: json_root.get("db_stg_devs", "")) {
    //   // Give enough max space for now. Mutant doesn't use it. With 200 GB, RocksDB will store all SSTables in the first path.
    //   options->db_paths.emplace_back(i[0].asString(), 200L*1024*1024*1024);
    // }



    exit(0);
    // TODO: now, a lot can be removed from the yaml file
    //
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
