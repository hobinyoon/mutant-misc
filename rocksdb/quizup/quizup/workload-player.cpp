#include <atomic>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <thread>

#include <boost/regex.hpp>
#include <boost/filesystem.hpp>

#include "conf.h"
#include "cons.h"
#include "db-client.h"
#include "prog-mon.h"
#include "simtime.h"
#include "workload-player.h"
#include "util.h"


using namespace std;


// Kernel time is too much. I'm guessing it's from rand(). Make a wrapper
// around this. The randomness decreases but, I think it's ok for the purpose.
void RandomAsciiString0(const int len, string& v) {
  vector<char> s(len);
  static const char alphanum[] =
    "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz";
  for (int i = 0; i < len; ++i) {
    s[i] = alphanum[rand() % (sizeof(alphanum) - 1)];
  }

  v = string(s.begin(), s.end());
}


void RandomAsciiString(const int len, string& v) {
  static bool big_rand_str_init = false;
  static string big_rand_str;
  // 10 M
  static const int big_rand_str_len = 100000000;
  static mutex init_m;
  if (!big_rand_str_init) {
    lock_guard<mutex> _(init_m);
    if (!big_rand_str_init) {
      RandomAsciiString0(big_rand_str_len, big_rand_str);
      big_rand_str_init = true;
    }
  }

  int remaining = len;

  while (remaining > 0) {
    int start_pos = rand() % (big_rand_str_len / 2);
    // 1M
    int len0 = 1000000;
    int len1 = min(remaining, len0);

    v += big_rand_str.substr(start_pos, len1);
    remaining -= len1;
  }
}


namespace WorkloadPlayer {

  struct TsOpOid {
    long ts;
    char op;
    long oid;

    TsOpOid()
      : ts(-1), op('-'), oid(-1)
    {}

    TsOpOid(ifstream& ifs) {
      ifs.read((char*)&ts, sizeof(ts));
      ifs.read(&op, sizeof(op));
      ifs.read((char*)&oid, sizeof(oid));
    }

    boost::posix_time::ptime TimeStamp() {
      // 160711170502871000
      // 012345678901234567
      //
      // 160711-170502.871000
      return Util::ToPtime(ts);
    }

    string ToString() const {
      // 229006591800701509
      // 012345678901234567
      return str(boost::format("%d %c %18d") % ts % op % oid);
    }
  };

  ostream& operator<<(ostream& os, const TsOpOid& too) {
    os << too.ToString();
    return os;
  }


  void _PlayWorkloadFile(const string& fn);
  void __PlayWorkloadFile(const string& fn);
  void _ArchiveLogs();
  void _CheckWorkloadData(const ifstream& ifs);


  int _value_len;

  atomic<int> _num_threads_ready_to_gen_requests(0);

  // Number of workers ready
  int _worker_ready = 0;
  mutex _worker_ready_mutex;
  condition_variable _worker_ready_cv;
  int _num_workers = 0;

  mutex _worker_start_generating_requests_mutex;
  condition_variable _worker_start_generating_requests_cv;
  bool _worker_start_generating_requests = false;

  atomic<bool> _stop_requested(false);


  // Play workload. The number of files decides the degree of parallelism.
  void Run() {
    vector<string> fns;
    // Get workload file list
    {
      string dn = Conf::GetDir("workload_dir");
      vector<string> fns1 = Util::ListDir(dn);
      int i = 0;
      boost::regex e(".+/\\d\\d\\d$");
      for (const auto& fn: fns1) {
        boost::smatch results;
        if (! boost::regex_match(fn, results, e))
          continue;

        fns.push_back(fn);
        // Useful for debugging
        if (false) {
          i ++;
          if (i == 3) {
            Cons::P(boost::format("Loaded %d for debugging") % i);
            break;
          }
        }
      }
      Cons::P(boost::format("Found %d files in %s") % fns.size() % dn);
      lock_guard<mutex> lk(_worker_ready_mutex);
      _num_workers = fns.size();
    }

    // Just checking the number of CPUs. Doesn't affect the parallelism.
    if (true) {
      int num_threads = thread::hardware_concurrency();
      Cons::P(boost::format("Found %d CPUs") % num_threads);
    }

    _value_len = Conf::Get("record_size").as<int>() - (8 + 18 + 8);
    if (_value_len <= 0)
      THROW("Unexpected");

    //Conf.Get("workload_stop_at").as<double>

    SimTime::Init1();

    vector<thread> threads;
    {
      Cons::MT _(boost::format("Initializing %d threads and optionally skipping some initial requests ...") % fns.size());
      for (size_t i = 0; i < fns.size(); i ++)
        threads.push_back(thread(_PlayWorkloadFile, fns[i]));

      // Wait for all threads to be ready
      {
        unique_lock<mutex> lk(_worker_ready_mutex);
        _worker_ready_cv.wait(lk, [](){return _worker_ready >= _num_workers;});
      }
    }

    SimTime::Init2();
    ProgMon::ReporterStart();

    {
      Cons::MT _("Generating requests ...");
      // Tell worker threads to go
      {
        unique_lock<mutex> lk(_worker_start_generating_requests_mutex);
        _worker_start_generating_requests = true;
      }
      _worker_start_generating_requests_cv.notify_all();

      for (auto& t: threads)
        t.join();
      ProgMon::ReporterStop();
    }

    _ArchiveLogs();
  }


  void Stop() {
    _stop_requested.exchange(true);
    SimTime::WakeupSleepingThreads();
  }


  // Read and make request one by one. Loading everything in memory can be too
  // much, especially on a EC2 node with limited memory.
  void _PlayWorkloadFile(const string& fn) {
    try {
      __PlayWorkloadFile(fn);
    } catch (const exception& e) {
      Cons::P(boost::format("Got an exception: %s") % e.what());
      exit(1);
    }
  }

  void __PlayWorkloadFile(const string& fn) {
    // WorkerStat that keeps stats of this thread. ProgMon reporter pulls the
    // statistics every so often.
    ProgMon::WorkerStat* ws = ProgMon::GetWorkerStat();

    ifstream ifs(fn, ios::binary);

    size_t s;
    ifs.read((char*) &s, sizeof(s));

    size_t i = 0;
    // Skip requests that are before workload_start_from
    if (SimTime::StartFromDefined()) {
      while (i < s) {
        TsOpOid too(ifs);
        i ++;
        if (SimTime::SimulatedTimeBeginLong() <= too.ts)
          break;
      }
    }

    // Notify the boss that this worker is ready to make requests.
    {
      lock_guard<mutex> lk(_worker_ready_mutex);
      ProgMon::IncTotalNumOps(s);
      _worker_ready ++;
    }
    _worker_ready_cv.notify_one();

    if (_stop_requested)
      return;

    // Wait for the boss to say go
    {
      unique_lock<mutex> lk(_worker_start_generating_requests_mutex);
      _worker_start_generating_requests_cv.wait(lk, [](){return _worker_start_generating_requests;});
    }

    //thread::id tid = this_thread::get_id();
    //string fn1 = boost::filesystem::path(fn).filename().string();
    //TRACE << boost::format("%d %s\n") % tid % fn1;

    // For the super read mode
    //   Extra memory estimation:
    //     (8 + 8 + 8) * 10000 * 1000 * 2 = 480 MB
    //                                  (for both deque and set)
    deque<long> latest_keys_q;
    //set<long> latest_keys_set;
    bool queue_size_printed = false;

    // Make requests
    while (i < s) {
      // Note: The first call to this by 1000 threads might be the bottleneck:
      // the reason that you see the 2-sec gap in the beginning. It's okay for
      // now.
      TsOpOid too(ifs);
      i ++;

      boost::posix_time::ptime too_ts = too.TimeStamp();

      if (SimTime::StopAtDefined()) {
        //Cons::P(boost::format("%s %s %s") % fn1 % too_ts % SimTime::SimulatedTimeStopAt());
        if (SimTime::SimulatedTimeStopAt() <= too_ts) {
          break;
        }
      }

      int phase = SimTime::MaySleepUntilSimulatedTime(too_ts, ws);
      if (_stop_requested)
        break;

      char k[20];
      sprintf(k, "%ld", too.oid);

      if (too.op == 'S') {
        string v;
        RandomAsciiString(_value_len, v);
        if (phase == 0) {
          DbClient::Put(k, v, ws);
        } else {
          DbClient::Put(k, v, ws);

          // Tried and dropped. No writes in the other phases. Didn't like pure random accesses.
					//   Cause it didn't show the proportionality between target_iops and latency. EBS st1 must have some internal cache.
        }
      } else if (too.op == 'G') {
        string v;

				latest_keys_q.push_front(too.oid);
				// Restrict the queue size
				if (latest_keys_q.size() > 2000) {
					latest_keys_q.pop_back();
				}

        if (phase == 0) {
          //if (latest_keys_set.find(too.oid) == latest_keys_set.end()) {
          //  latest_keys_set.insert(too.oid);
          //  latest_keys_q.push_front(too.oid);
          //  // Restrict the queue size
          //  if (latest_keys_q.size() > 20000) {
          //    latest_keys_set.erase(*latest_keys_q.rbegin());
          //    latest_keys_q.pop_back();
          //  }
          //}
        } else if (phase >= 1) {
					DbClient::Get(k, v, ws);

          size_t s = latest_keys_q.size();

          if (phase == 1) {
            DbClient::SetSstOtt(10.0);
          } else if (phase == 2) {
            DbClient::SetSstOtt(100.0);
          } else if (phase >= 3) {
            DbClient::SetSstOtt(400.0);
          }

          //if (! queue_size_printed) {
          //  Cons::P(boost::format("latest_keys_q.size()=%d") % s);
          //  queue_size_printed = true;
          //}

          //for (int i = 0; i < phase * 1; i ++) {
          for (int i = 0; i < 50; i ++) {
            long oid = latest_keys_q[rand() % s];
            char k1[20];
            sprintf(k1, "%ld", oid);
            DbClient::Get(k1, v, ws);
          }
        }
      } else {
        THROW(boost::format("Unexpected op %c") % too.op);
      }
    }
  }


  // Copy the DB LOG file and client log file to log archive directory, and zip
  // them.
  //
  // Archiving logs here is easier so that we don't have to pass the
  // simulation_time_begin to the calling script.
  void _ArchiveLogs() {
    Cons::MT _("Archiving logs ...");

    string sbt = Util::ToString(SimTime::SimulationTime0());

    // DB LOG
    string fn_db0 = str(boost::format("%s/LOG") % Conf::GetDir("db_path"));
    string dn1 = str(boost::format("%s/rocksdb") % Conf::GetDir("log_archive_dn"));
    string fn_db1 = str(boost::format("%s/%s") % dn1 % sbt);
    boost::filesystem::create_directories(dn1);
    boost::filesystem::copy_file(fn_db0, fn_db1);

    // QuizUp client log
    const string& fn_c0 = ProgMon::FnClientLog();
    dn1 = str(boost::format("%s/quizup") % Conf::GetDir("log_archive_dn"));
    string fn_c1 = str(boost::format("%s/%s") % dn1 % sbt);
    boost::filesystem::create_directories(dn1);
    boost::filesystem::copy_file(fn_c0, fn_c1);

    // Zip them
    Util::RunSubprocess(str(boost::format("7z a -mx %s.7z %s >/dev/null 2>&1") % fn_db1 % fn_db1));
    // Quizup client log will be zipped by the calling script after the configuration parameters added.
    //Util::RunSubprocess(str(boost::format("7z a -mx %s.7z %s >/dev/null 2>&1") % fn_c1 % fn_c1));
  }


  void _CheckWorkloadData(ifstream& ifs, size_t s, const string& fn) {
    // Check data: oldest and newest ones
    TsOpOid first;
    bool first_set = false;
    TsOpOid last;

    for (size_t i = 0; i < s; i ++) {
      TsOpOid too(ifs);
      if (! first_set) {
        first = too;
        first_set = true;
      }
      last = too;
    }
    Cons::P(boost::format("%s %8d %s %s %d")
        % boost::filesystem::path(fn).filename().string()
        % boost::filesystem::file_size(fn)
        % first % last
        % (first.oid == last.oid)
        );
  }

}
