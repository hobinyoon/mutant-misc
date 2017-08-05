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


namespace Serial {
	map<string, int> obj_num_r;
	map<string, int> obj_num_w;

	void ReadFile(const string& fn) {
		Cons::MT _(boost::format("Reading file %s ...") % fn);

		std::ifstream ifs(fn);
		auto sep = boost::is_any_of(" ");
		for(string line; getline(ifs, line); ) {
			vector<string> t;
			boost::split(t, line, sep);
			if (t.size() != 3)
				THROW(boost::format("Unexpected %s") % line);
			//const string& ts = t[0];
			const string& op = t[1];
			const string& obj_id = t[2];
			//Cons::P(boost::format("%s %s %s") % ts % op % obj_id);

			if (op == "G") {
				auto it = obj_num_r.find(obj_id);
				if (it == obj_num_r.end()) {
					obj_num_r[obj_id] = 1;
				} else {
					obj_num_r[obj_id] += 1;
				}
			} else if (op == "S") {
				auto it = obj_num_w.find(obj_id);
				if (it == obj_num_w.end()) {
					obj_num_w[obj_id] = 1;
				} else {
					obj_num_w[obj_id] += 1;
				}
			} else {
				THROW("Unexpected");
			}
		}
	}


	void Count() {
		vector<string> fns = Util::ListDir(boost::regex_replace(Conf::GetStr("in_dir"),
					boost::regex("~"), Util::HomeDir()));

		for (const auto& fn: fns)
			ReadFile(fn);
	}
};


namespace Parallel {
	ConcurrentQ<string> _q;
	map<string, int> _obj_num_r;
	map<string, int> _obj_num_w;
	mutex _lock_r;
	mutex _lock_w;

	void MergeCnt(const map<string, int>& obj_num_r,
			const map<string, int>& obj_num_w) {
		{
			lock_guard<mutex> _(_lock_r);
			for (auto it: obj_num_r) {
				const string& k = it.first;
				const int v = it.second;

				auto it2 = _obj_num_r.find(k);
				if (it2 == _obj_num_r.end()) {
					_obj_num_r[k] = v;
				} else {
					it2->second += v;
				}
			}
		}

		{
			lock_guard<mutex> _(_lock_w);
			for (auto it: obj_num_w) {
				const string& k = it.first;
				const int v = it.second;

				auto it2 = _obj_num_w.find(k);
				if (it2 == _obj_num_w.end()) {
					_obj_num_w[k] = v;
				} else {
					it2->second += v;
				}
			}
		}
	}

	void ReadFile() {
		map<string, int> obj_num_r;
		map<string, int> obj_num_w;

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
				//const string& ts = t[0];
				const string& op = t[1];
				const string& obj_id = t[2];

				if (op == "G") {
					auto it = obj_num_r.find(obj_id);
					if (it == obj_num_r.end()) {
						obj_num_r[obj_id] = 1;
					} else {
						obj_num_r[obj_id] += 1;
					}
				} else if (op == "S") {
					auto it = obj_num_w.find(obj_id);
					if (it == obj_num_w.end()) {
						obj_num_w[obj_id] = 1;
					} else {
						obj_num_w[obj_id] += 1;
					}
				} else {
					THROW("Unexpected");
				}
			}

			Cons::P(boost::format("Read file %s in %.0f ms")
					% fn % (tmr.elapsed().wall / 1000000.0));
		}

		MergeCnt(obj_num_r, obj_num_w);
	}

	void Report() {
		// Number of unique objects (users)
		size_t num_objs;
		{
			set<string> objs;
			for (const auto it: _obj_num_r)
				objs.insert(it.first);
			for (const auto it: _obj_num_w)
				objs.insert(it.first);
			num_objs = objs.size();
		}

		{
			vector<int> cnts;
			for (const auto it: _obj_num_r)
				cnts.push_back(it.second);

			string fn = str(boost::format("%s/num-reads-by-obj-ranks")
				% boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
			ofstream ofs(fn);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % fn);
			ofs << boost::format("# num_objs: %d (some have 0 read)\n") % num_objs;
			ofs << "#\n";
			Stat::ByRank<int>(cnts, ofs);
			ofs.close();
			Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
		}
		{
			vector<int> cnts;
			for (const auto it: _obj_num_w)
				cnts.push_back(it.second);

			string fn = str(boost::format("%s/num-writes-by-obj-ranks")
				% boost::regex_replace(Conf::GetStr("out_dir"), boost::regex("~"), Util::HomeDir()));
			ofstream ofs(fn);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % fn);
			ofs << boost::format("# num_objs: %d (some have 0 write)\n") % num_objs;
			ofs << "#\n";
			Stat::ByRank<int>(cnts, ofs);
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
				if (i == 2)
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

		//Serial::Count();
		Parallel::Count();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
