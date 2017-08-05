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


namespace Parallel {
	ConcurrentQ<string> _q;

	// map<time_in_20min_granularity, num_reads>
	// map<time_in_20min_granularity, num_writes>
	map<string, int> _time_num_r;
	map<string, int> _time_num_w;
	mutex _lock_r;
	mutex _lock_w;

	void MergeCnt(const map<string, int>& time_num_r,
			const map<string, int>& time_num_w) {
		{
			lock_guard<mutex> _(_lock_r);
			for (auto it: time_num_r) {
				const string& k = it.first;
				const int v = it.second;

				auto it2 = _time_num_r.find(k);
				if (it2 == _time_num_r.end()) {
					_time_num_r[k] = v;
				} else {
					it2->second += v;
				}
			}
		}

		{
			lock_guard<mutex> _(_lock_w);
			for (auto it: time_num_w) {
				const string& k = it.first;
				const int v = it.second;

				auto it2 = _time_num_w.find(k);
				if (it2 == _time_num_w.end()) {
					_time_num_w[k] = v;
				} else {
					it2->second += v;
				}
			}
		}
	}

	void ReadFile() {
		map<string, int> time_num_r;
		map<string, int> time_num_w;

		while (true) {
			boost::timer::cpu_timer tmr;

			string fn;
			try {
				fn = _q.Pop();
			} catch (const ConQEmpty& e) {
				break;
			}

			std::ifstream ifs(fn);
			static const auto sep = boost::is_any_of(" ");
			for(string line; getline(ifs, line); ) {
				vector<string> t;
				boost::split(t, line, sep);
				if (t.size() != 3)
					THROW(boost::format("Unexpected %s") % line);
				// 160727-114045.000000
				// 01234567890123456789
				string ts = t[0].substr(0, 9);
				// 20-minute granularity. For example,
				//   160727-113045.000000 becomes
				//   160727-112
				ts += ((((t[0][9] - '0') / 2) * 2) + '0');
				ts += '0';
				const string& op = t[1];
				//const string& obj_id = t[2];
				//Cons::P(boost::format("%s %s %s") % ts % op % obj_id);

				if (op == "G") {
					auto it = time_num_r.find(ts);
					if (it == time_num_r.end()) {
						time_num_r[ts] = 1;
					} else {
						time_num_r[ts] += 1;
					}
				} else if (op == "S") {
					auto it = time_num_w.find(ts);
					if (it == time_num_w.end()) {
						time_num_w[ts] = 1;
					} else {
						time_num_w[ts] += 1;
					}
				} else {
					THROW("Unexpected");
				}
			}

			Cons::P(boost::format("Read file %s in %.0f ms")
					% fn % (tmr.elapsed().wall / 1000000.0));
		}

		MergeCnt(time_num_r, time_num_w);
	}

	void Report() {
		{
			string fn = str(boost::format("%s/num-reads-by-time")
				% boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
			ofstream ofs(fn);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % fn);
			for (const auto it: _time_num_r)
				ofs << boost::format("%s %d\n") % it.first % it.second;
			ofs.close();
			Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
		}
		{
			string fn = str(boost::format("%s/num-writes-by-time")
				% boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
			ofstream ofs(fn);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % fn);
			for (const auto it: _time_num_w)
				ofs << boost::format("%s %d\n") % it.first % it.second;
			ofs.close();
			Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
		}
	}

	void Count() {
		vector<string> fns = Util::ListDir(boost::regex_replace(Conf::GetStr("in_dir"),
					boost::regex("~"), Util::HomeDir()));
		int i = 0;
		for (const auto& fn: fns) {
			_q.Push(fn);
			// Useful for debugging
			if (false) {
				i ++;
				if (i == 3)
					break;
			}
		}

 		int num_threads = thread::hardware_concurrency();
 		Cons::P(num_threads);

 		vector<thread> threads;
 		for (int i = 0; i < num_threads; i ++)
 			threads.push_back(thread(ReadFile));
 		for (auto& t: threads)
 			t.join();

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

		Parallel::Count();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
