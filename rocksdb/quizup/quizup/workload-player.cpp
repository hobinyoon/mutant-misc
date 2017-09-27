#include <atomic>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

#include <boost/algorithm/string.hpp>
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
  int _xr_gets_per_key = 0;
  int _xr_sleep_upper_bound_ms[3];

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

    // Pre-calculate additional parameters
    static const auto sep = boost::is_any_of(":");
    vector<string> xr_iops;
    boost::split(xr_iops, Conf::GetStr("xr_iops"), sep);
    if (xr_iops.size() != 3)
      THROW(boost::format("Unexpected %d") % xr_iops.size());

    _xr_gets_per_key = Conf::Get("xr_gets_per_key").as<int>();
    // 1000.0: ms
    // * 2: upper bound
    // * 1000: 1000 threads

    for (int i = 0; i < 3; i ++) {
      _xr_sleep_upper_bound_ms[i] = int((1000.0 / (atof(xr_iops[i].c_str()) / _xr_gets_per_key)) * 2 * 1000);
      Cons::P(boost::format("# _xr_sleep_upper_bound_ms[%d]=%d") % i % _xr_sleep_upper_bound_ms[i]);
    }

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
    const bool req_extra_reads = Conf::Get("extra_reads").as<bool>();
    deque<long> latest_keys_q;
    set<long> latest_keys_set;
    bool uniform_key_popularity = true;
    const size_t latest_keys_q_cap = Conf::Get("xr_queue_size").as<int>();
    boost::posix_time::ptime prev_ts_queue_size_report;
    // From phase2, make uniform random, uniformly placed requests until the end of the simulation time.
    bool phase2_started = false;

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
        DbClient::Put(k, v, ws);

        // Tried and dropped. No writes in the other phases. Didn't like pure random accesses.
        //   Cause it didn't show the proportionality between target_iops and latency. EBS st1 must have some internal cache.
      } else if (too.op == 'G') {
        if (req_extra_reads) {
          if (uniform_key_popularity) {
            if (latest_keys_set.find(too.oid) == latest_keys_set.end()) {
              latest_keys_set.insert(too.oid);
              latest_keys_q.push_front(too.oid);
              // Restrict the queue size
              if (latest_keys_q.size() > latest_keys_q_cap) {
                latest_keys_set.erase(*latest_keys_q.rbegin());
                latest_keys_q.pop_back();
              }
            }
          } else {
            latest_keys_q.push_front(too.oid);
            // Restrict the queue size
            if (latest_keys_q.size() > latest_keys_q_cap) {
              latest_keys_q.pop_back();
            }
          }

          // Update the queue length every second
          {
            boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
            if (prev_ts_queue_size_report.is_not_a_date_time()) {
              prev_ts_queue_size_report = now;
            } else {
              if (1000 < (now - prev_ts_queue_size_report).total_milliseconds()) {
                ProgMon::UpdateXrQLen(latest_keys_q.size());
                prev_ts_queue_size_report = now;
              }
            }
          }
        }

        if (phase == 0) {
          // No reads during the load phase
        } else if (1 <= phase) {
          string v;
          DbClient::Get(k, v, ws);

          if (phase == 1) {
          } else if (phase == 2) {
            ProgMon::StartReportingToSlaAdmin();
            phase2_started = true;
            break;
          }
        }
      } else {
        THROW(boost::format("Unexpected op %c") % too.op);
      }
    }

    if (phase2_started && req_extra_reads) {
      size_t q_size = latest_keys_q.size();
      if (q_size == 0) {
        // Nothing to do
      } else {
        while (! _stop_requested) {
          boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
          int read_121_phase = 0;
          if (now < SimTime::SimulationTime3()) {
            read_121_phase = 0;
          } else if (now < SimTime::SimulationTime4()) {
            read_121_phase = 1;
          } else {
            read_121_phase = 2;
          }
          int sleep_ms = rand() % _xr_sleep_upper_bound_ms[read_121_phase];

          if (SimTime::SimulationTimeEnd() <= now + boost::posix_time::milliseconds(sleep_ms))
            break;
          SimTime::SleepFor(sleep_ms);
          if (_stop_requested)
            break;

          long oid = latest_keys_q[rand() % q_size];
          char k1[20];
          sprintf(k1, "%ld", oid);
          string v;
          for (int i = 0; i < _xr_gets_per_key; i ++)
            DbClient::Get(k1, v, ws);
        }
      }
    }
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
