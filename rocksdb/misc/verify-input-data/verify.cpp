#include <atomic>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <thread>

#include <boost/regex.hpp>

#include "concurrent-q.h"
#include "conf.h"
#include "cons.h"
#include "prog-mon.h"
#include "simtime.h"
#include "util.h"
#include "verify.h"


using namespace std;


namespace Verify {

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


void _VerifyFiles();
void _VerifyFile(const string& fn);
void _DumpFile(const string& fn);
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


ConcurrentQ<string> _q;

// Verify that
// - records are in the ts order
// - records intermixed by different obj_id(s)
void Run() {
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

			_q.Push(fn);
			// Useful for debugging
			if (false) {
				i ++;
				if (i == 3) {
					Cons::P(boost::format("Loaded %d for debugging") % i);
					break;
				}
			}
		}
		Cons::P(boost::format("Found %d files in %s") % _q.Size() % dn);

		lock_guard<mutex> lk(_worker_ready_mutex);
		_num_workers = _q.Size();
	}

	int num_cpus = thread::hardware_concurrency();
	Cons::P(boost::format("Found %d CPUs") % num_cpus);

	// For debugging. Use with _DumpFile() below
	if (false)
		num_cpus = 1;

	vector<thread> threads;
	for (size_t i = 0; i < num_cpus; i ++)
		threads.push_back(thread(_VerifyFiles));
	for (auto& t: threads)
		t.join();
}


void Stop() {
	_stop_requested.exchange(true);
	SimTime::WakeupSleepingThreads();
}


// Read and make request one by one. Loading everything in memory can be too
// much, especially on a EC2 node with limited memory.
void _VerifyFiles() {
	try {
		while (true) {
			string fn;
			try {
				fn = _q.Pop();
			} catch (const ConQEmpty& e) {
				break;
			}
			_VerifyFile(fn);
			//_DumpFile(fn);
		}
	} catch (const exception& e) {
		Cons::P(boost::format("Got an exception: %s") % e.what());
		exit(1);
	}
}


void _VerifyFile(const string& fn) {
	//Cons::MT _(boost::format("Verifying %s ...") % fn);
	boost::timer::cpu_timer tmr;

	ifstream ifs(fn, ios::binary);

	size_t s;
	ifs.read((char*) &s, sizeof(s));

	TsOpOid* too_prev = NULL;

	bool do_histogram = false;

	// map<oid, map<histo_dist_from_last_oid, cnt> >
	map<long , map<int, int> > oid_dist_histo;

	// map<oid, last_pos>
	map<long , size_t> oid_lastpos;

	for (size_t i = 0; i < s; i ++) {
		TsOpOid* too = new TsOpOid(ifs);

		if (too_prev) {
			if (too_prev->ts > too->ts) {
				THROW(boost::format("[%s] [%s]") % *too_prev % *too);
				// Caught an error!
				// [160727121555772632 G 395893451423586438] [160716055518961815 S 499359422661863438]
			}
		}

		if (do_histogram) {
			auto it = oid_lastpos.find(too->oid);
			if (it != oid_lastpos.end()) {
				size_t lastpos = it->second;
				int dist = i - lastpos;

				auto it2 = oid_dist_histo.find(too->oid);
				if (it2 == oid_dist_histo.end())
					oid_dist_histo[too->oid] = map<int, int>();
				auto it3 = oid_dist_histo[too->oid].find(dist);
				if (it3 == oid_dist_histo[too->oid].end()) {
					oid_dist_histo[too->oid][dist] = 1;
				} else {
					it3->second ++;
				}
			}

			oid_lastpos[too->oid] = i;
		}

		if (too_prev)
			delete too_prev;
		too_prev = too;
	}
	if (too_prev)
		delete too_prev;

	// Print out the histogram
	if (do_histogram) {
		for (auto i: oid_dist_histo) {
			stringstream ss;
			long oid = i.first;
			ss << oid << ":";
			for (auto j: i.second)
				ss << boost::format(" %d:%d") % j.first % j.second;
			Cons::P(ss.str());
		}
	}

	Cons::P(boost::format("Checked file %s in %.0f ms")
			% fn % (tmr.elapsed().wall / 1000000.0));
}


// I can clearly see that objects are sorted by their obj_ids first and by
// their ts! Error detected!
void _DumpFile(const string& fn) {
	Cons::MT _(boost::format("Dumping %s ...") % fn);

	ifstream ifs(fn, ios::binary);

	size_t s;
	ifs.read((char*) &s, sizeof(s));

	for (size_t i = 0; i < s; i ++) {
		TsOpOid too(ifs);
		Cons::P(too.ToString());
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
