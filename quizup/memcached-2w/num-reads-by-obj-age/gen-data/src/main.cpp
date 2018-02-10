#include <signal.h>
#include <unistd.h>
#include <iostream>
#include <queue>
#include <thread>

#include <boost/algorithm/string.hpp>
#include <boost/regex.hpp>

#include "concurrent-q.h"
#include "conf.h"
#include "cons.h"
#include "stat.h"
#include "util.h"


using namespace std;


void on_signal(int sig) {
  cout << boost::format("\nGot a signal: %d\n%s\n") % sig % Util::Indent(Util::StackTrace(1), 2);
  exit(1);
}


struct OidUt {
  long oid;
  string last_update_time;

  OidUt(long oid_, string last_update_time_)
  : oid(oid_), last_update_time(last_update_time_)
  { }

  bool operator < (const OidUt& r) const {
    if (oid < r.oid)
      return true;
    else if (oid > r.oid)
      return false;
    return (last_update_time < r.last_update_time);
  }
};


namespace Serial {
  // Can I assume the obj_id is a 64-bit number? Seems like. Checked 2 5MB files.
  //
  // Aggregate access counts by obj ages. Age starts from the last upate time.
  // Age granularity is 1 min.
  //
  // map< age, cnt >
  map<long, int> _age_cnt;

  // We don't need this. At least in the paper.
  //
  // Obj age starts either from the first write or from the beginning of the traces. Not from the last update.
  //
  // map< OidUt, map<age, cnt> >
  map<OidUt, map<long, int> > _ou_age_cnt;

  // Note: Records are updated in full, not only a subset of columes are
  // updated, which can complicate record reads in Cassandra.  It's with a
  // key-value store like LevelDB or RocksDB. Let's make it simple.
  //
  // Otherwise, which is in general case, you need to look for all SSTables for
  // the given key. You can't early terminate.  In Cassandra, this can be
  // avoided by deleting and inserting the record.
  
  // We set the last update time of an unseen object to the beginning of the traces.
  //
  // This is what makes the parallelization hard.
  //   Because input files are split by the time, you can't process the next ones before finishing the previous one.
  //   Unless you reorganize the input files by obj IDs.
  //   Serial processing takes about 3.5 hours. So, may not be worth the effort.
  map<long, string> _oid_utime;

  bool _ts_begin_set = false;
  string _ts_begin;

  // Returns the timestamp diff in us. Format:
  //   160727-114045.001108
  //   01234567890123456789
  // We do a light-weight ts subtraction, since we know the range.
  long TsDiff(const string& ts1, const string& ts0) {
    long t1, t0;
    {
      long d = atol(ts0.substr(4, 2).c_str());
      long h = atol(ts0.substr(7, 2).c_str());
      long m = atol(ts0.substr(9, 2).c_str());
      long s = atol(ts0.substr(11, 2).c_str());
      long us = atol(ts0.substr(14).c_str());
      t0 = d * 24 * 60 * 60 * 1000000
        + h       * 60 * 60 * 1000000
        + m            * 60 * 1000000
        + s                 * 1000000
        + us;
    }
    {
      long d = atol(ts1.substr(4, 2).c_str());
      long h = atol(ts1.substr(7, 2).c_str());
      long m = atol(ts1.substr(9, 2).c_str());
      long s = atol(ts1.substr(11, 2).c_str());
      long us = atol(ts1.substr(14).c_str());
      t1 = d * 24 * 60 * 60 * 1000000
        + h       * 60 * 60 * 1000000
        + m            * 60 * 1000000
        + s                 * 1000000
        + us;
    }
    return t1 - t0;
  }

  void ReadFile(const string& fn) {
    boost::timer::cpu_timer tmr;

    std::ifstream ifs(fn);
    static const auto sep = boost::is_any_of(" ");
    for (string line; getline(ifs, line); ) {
      vector<string> t;
      boost::split(t, line, sep);
      if (t.size() != 3)
        THROW(boost::format("Unexpected %s") % line);
      // 160727-114045.001108
      // 01234567890123456789
      //
      // 875823725596562742
      const string& ts = t[0];
      const string& op = t[1];
      const long obj_id = atol(t[2].c_str());
      //Cons::P(boost::format("%s %s %s") % ts % op % obj_id);

      if (!_ts_begin_set) {
        _ts_begin = ts;
        _ts_begin_set = true;
      }

      if (op == "S") {
        _oid_utime[obj_id] = ts;
      } else if (op == "G") {
        auto it = _oid_utime.find(obj_id);
        // We don't count "gets" those have never "set" before. It distorts the
        // statistics.
        if (it == _oid_utime.end())
          continue;
        string last_u_time = it->second;

        // Timestamp diff in minutes in 1 min granularity
        long ts_diff = TsDiff(ts, last_u_time) / (60L * 1000000);
        {
          // Update aggregate cnts by obj ages
          auto it2 = _age_cnt.find(ts_diff);
          if (it2 == _age_cnt.end()) {
            _age_cnt[ts_diff] = 1;
          } else {
            it2->second += 1;
          }
        }

        {
          // Update per (object, last update time) cnts by obj ages
          OidUt ou(obj_id, last_u_time);
          auto it2 = _ou_age_cnt.find(ou);
          if (it2 == _ou_age_cnt.end()) {
            _ou_age_cnt[ou] = map<long, int>();
          }
          auto it3 = _ou_age_cnt[ou].find(ts_diff);
          if (it3 == _ou_age_cnt[ou].end()) {
            _ou_age_cnt[ou][ts_diff] = 1;
          } else {
            it3->second += 1;
          }
        }
      } else {
        THROW("Unexpected");
      }
    }

    Cons::P(boost::format("Read file %s %d in %.0f ms")
        % fn % boost::filesystem::file_size(fn) % (tmr.elapsed().wall / 1000000.0));
  }


  void Report() {
    {
      // Aggregated stat
      string fn = str(boost::format("%s/num-reads-by-obj-age")
        % boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
      ofstream ofs(fn);
      if (! ofs.is_open())
        THROW(boost::format("Unable to open file %s") % fn);
      for (auto i: _age_cnt)
        ofs << boost::format("%d %d\n") % i.first % i.second;
      ofs.close();
      Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
    }
    {
      // Generate per-object per-last-update-time access popularity by obj age
      string dn = str(boost::format("%s/num-reads-by-obj-by-lastupdatetime-by-obj-age")
        % boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
      boost::filesystem::create_directories(dn);

      ofstream* ofs = NULL;
      long oid_prev = -1;
      long oid_group_prev = -1;
      string fn;
      for (auto i: _ou_age_cnt) {
        long oid = i.first.oid;
        const string& last_update_time = i.first.last_update_time;

        // 654776985889737744
        //   1000000000000000
        long oid_group = oid / 1000000000000000L;
        if (oid_group != oid_group_prev) {
          if (ofs != NULL) {
            ofs->close();
            delete ofs;
            Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
          }

          fn = str(boost::format("%s/%03d") % dn % oid_group);
          ofs = new ofstream(fn);
          if (! ofs->is_open())
            THROW(boost::format("Unable to open file %s") % fn);

          oid_group_prev = oid_group;
          oid_prev = -1;
        }

        if (oid_prev == -1) {
          *ofs << oid << "\n";
          oid_prev = oid;
        } else {
          if (oid != oid_prev) {
            *ofs << "\n";
            *ofs << oid << "\n";
            oid_prev = oid;
          }
        }

        *ofs << last_update_time;
        for (auto i2: i.second) {
          *ofs << boost::format(" %d %d") % i2.first % i2.second;
        }
        *ofs << "\n";
      }

      if (ofs != NULL) {
        ofs->close();
        delete ofs;
        Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
      }
    }
  }


  void GenStat() {
    vector<string> fns = Util::ListDir(boost::regex_replace(Conf::GetStr("in_dir"),
          boost::regex("~"), Util::HomeDir()));
    sort(fns.begin(), fns.end());
    // Useful for debugging
    if (false)
      fns.resize(20);

    for (const auto& fn: fns)
      ReadFile(fn);

    Report();
  }
};


int main(int argc, char* argv[]) {
  try {
    signal(SIGSEGV, on_signal);
    signal(SIGINT, on_signal);

    Conf::Init(argc, argv);

    boost::filesystem::create_directories(
        boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"),
          Util::HomeDir()));

    Serial::GenStat();
  } catch (const exception& e) {
    cerr << "Got an exception: " << e.what() << "\n";
    return 1;
  }
  return 0;
}
