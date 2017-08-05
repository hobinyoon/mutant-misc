#include <functional>
#include <iostream>
#include <map>
#include <queue>
#include <thread>

#include <boost/algorithm/string.hpp>
#include <boost/regex.hpp>

#include "concurrent-q.h"
#include "cons.h"
#include "conf.h"
#include "generator.h"
#include "util.h"

using namespace std;

namespace Gen {
	ConcurrentQ<string> _q;

	struct TsOp {
		long ts;
		char op;

		TsOp(long ts_, char op_)
			: ts(ts_), op(op_)
		{}

		bool operator< (const TsOp& r) const {
			return (ts < r.ts);
		}
	};


	map<long, vector<TsOp> > _oid_tsop;
	mutex _oid_tsop_lock;

	void _Merge(const map<long, vector<TsOp> >& oid_tsop) {
		lock_guard<mutex> _(_oid_tsop_lock);

		for (auto i: oid_tsop) {
			long oid = i.first;

			auto it = _oid_tsop.find(oid);
			if (it == _oid_tsop.end()) {
				_oid_tsop[oid] = i.second;
			} else {
				it->second.insert(it->second.end(), i.second.begin(), i.second.end());
			}
		}
	}


	void ReadFile() {
		try {
			while (true) {
				string fn;
				try {
					fn = _q.Pop();
				} catch (const ConQEmpty& e) {
					break;
				}

				// map<obj_id, vector<(ts, op)> >
				map<long, vector<TsOp> > oid_tsop;

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
					const string& ts_str = t[0];
					const long ts = atol(ts_str.substr(0, 6).c_str()) * 1000000000000L
						+ atol(ts_str.substr(7, 6).c_str()) * 1000000L
						+ atol(ts_str.substr(14, 6).c_str());
					const char op = t[1][0];
					const long obj_id = atol(t[2].c_str());
					//Cons::P(boost::format("%s %s %s") % ts % op % obj_id);

					auto it = oid_tsop.find(obj_id);
					if (it == oid_tsop.end())
						oid_tsop[obj_id] = vector<TsOp>();
					oid_tsop[obj_id].push_back(TsOp(ts, op));
				}

				Cons::P(boost::format("Read file %s %d in %.0f ms. %d obj_id(s)")
						% fn % boost::filesystem::file_size(fn) % (tmr.elapsed().wall / 1000000.0)
						% oid_tsop.size()
						);

				_Merge(oid_tsop);
			}
		} catch (const exception& e) {
			Cons::P(boost::format("Got an exception: %s") % e.what());
			exit(1);
		}
	}


	const int _num_files = 1000;
	double _output_percentage;
	string _dn_out;

	void _Init() {
		// Generate output directory so that you can terminate early in case of an
		// error.
		_output_percentage = Conf::Get("output_percentage").as<double>();
		Cons::P(boost::format("_output_percentage=%f") % _output_percentage);

		_dn_out = str(boost::format("%s/%.2f")
				% boost::regex_replace(Conf::GetStr("dn_out"), boost::regex("~"), Util::HomeDir())
				% _output_percentage);
		boost::filesystem::create_directories(_dn_out);
	}


	struct TsOpOid {
		long ts;
		char op;
		long oid;

		TsOpOid(long ts_, char op_, long oid_)
			: ts(ts_), op(op_), oid(oid_)
		{}

		bool operator< (const TsOpOid& r) const {
			return (ts < r.ts);
		}

		void Write(ofstream& ofs) {
			ofs.write((char*)&ts, sizeof(ts));
			ofs.write(&op, sizeof(op));
			ofs.write((char*)&oid, sizeof(oid));
		}

		string ToString() {
			return str(boost::format("%d %c %d") % ts % op % oid);
		}
	};


	// Balance the number of items in each bucket
	const size_t _num_buckets = 1000;
	auto _size_bucket_less_than = [](const vector<TsOpOid>* l, const vector<TsOpOid>* r) { return (l->size() > r->size());};
	priority_queue<vector<TsOpOid>*, vector<vector<TsOpOid>* >, decltype(_size_bucket_less_than)> _buckets(_size_bucket_less_than);


	void _GenOutputData() {
		Cons::MT _("Generating output data ...");

		// Initialize _buckets
		for (size_t i = 0; i < _num_buckets; i ++) {
			vector<TsOpOid>* b = new vector<TsOpOid>();
			_buckets.push(b);
		}

		for (auto i: _oid_tsop) {
			// Filter data with the percentage
			if (drand48() > (_output_percentage / 100.0))
				continue;

			// Get the bucket with the smallest size
			vector<TsOpOid>* b = _buckets.top();
			_buckets.pop();

			long oid = i.first;
			auto& tsops = i.second;
			sort(tsops.begin(), tsops.end());
			// Use the same ts for the missing first write. It's fine for the
			// purpose. Subtracting 1us in the encoded long is not a trivial.
			if (tsops[0].op == 'G')
				b->push_back(TsOpOid(tsops[0].ts, 'S', oid));
			// Copy the remaining operations.
			for (auto j: tsops)
				b->push_back(TsOpOid(j.ts, j.op, oid));

			// Put the bucket back
			_buckets.push(b);
		}
	}


	void _GenOutputFiles() {
		Cons::MT _("Generating output files ...");

		Cons::P(boost::format("Total %d objects") % _oid_tsop.size());

		int i = 0;
		while (!_buckets.empty()) {
			vector<TsOpOid>* b = _buckets.top();
			_buckets.pop();
			if (b->size() == 0)
				continue;

			string fn = str(boost::format("%s/%03d") % _dn_out % i);
			ofstream ofs(fn, ios::binary);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % fn);
			//Cons::P(i);

			size_t s = b->size();
			ofs.write((char*) &s, sizeof(s));

			// Stable-sort entries by ts
			stable_sort(b->begin(), b->end());

			for (auto j: *b) {
				j.Write(ofs);
				//Cons::P(j.ToString());
			}
			ofs.close();
			Cons::P(boost::format("Created %s %d") % fn % boost::filesystem::file_size(fn));

			delete b;
			i ++;
		}
	}


	void Run() {
		_Init();

		vector<string> fns = Util::ListDir(boost::regex_replace(Conf::GetStr("dn_in"),
					boost::regex("~"), Util::HomeDir()));
		int i = 0;
		boost::regex e(".+/\\d\\d\\d\\d\\d\\d-\\d\\d\\d\\d\\d\\d$");
		for (const auto& fn: fns) {
			// Include, if the last 4 chars are /\d\d\d
			//boost::match_results<string::const_iterator> results;
			boost::smatch results;
			if (! boost::regex_match(fn, results, e))
				continue;

			_q.Push(fn);
			// Useful for debugging
			if (false) {
				i ++;
				if (i == 48) {
					Cons::P(boost::format("Loaded %d for debugging") % i);
					break;
				}
			}
		}
		Cons::P(boost::format("Found %d input files") % _q.Size());

 		int num_cpus = thread::hardware_concurrency();
 		Cons::P(boost::format("Found %d CPUs") % num_cpus);

		{
			Cons::MT _("Reading input files ...");
			vector<thread> threads;
			for (int i = 0; i < num_cpus; i ++)
				threads.push_back(thread(ReadFile));
			for (auto& t: threads)
				t.join();
		}

		_GenOutputData();
		_GenOutputFiles();
	}
};

