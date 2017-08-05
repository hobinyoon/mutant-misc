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

string _dn_out;


void on_signal(int sig) {
	cout << boost::format("\nGot a signal: %d\n%s\n") % sig % Util::Indent(Util::StackTrace(1), 2);
  exit(1);
}


namespace Parallel {
	ConcurrentQ<string> _q;

	// temp_drop_alpha: temperature drop smoothing factor. Temperature decays by 0.9 every
	// minute. Seems like a reasonable one. Temp 1 drops to 0.001 in 72 mins,
	// about 1.5 hours.
	const double temp_drop_alpha = 0.9;

	// Temp 1 drops to 0.001 in 72 mins, about 1.5 hours.
	const double become_cold_temp_threshold = 0.001;

	struct UtAgeCnts {
		string last_update_time;
		// map< age, cnt >
		map<long, int> age_cnt;
		//map<long, double> age_temp;

		bool passed_initial_peak = false;

		// 0 means 1-min time interval
		long initial_hot_region_length_until_last_req = -1;
		long initial_hot_region_length_until_cold = -1;

		void _CalcTempByAge() {
			// Calculate temperature by time with exponential smoothing.
			//   https://en.wikipedia.org/wiki/Exponential_smoothing

			// t: current temperature
			double t = 0.0;
			long prev_age = -1;
			for (auto i: age_cnt) {
				long age = i.first;
				int cnt = i.second;

				if (prev_age == -1) {
					t = cnt * (1.0 / (1.0 - temp_drop_alpha));
				} else {
					// 2. Check if the temperature drops
					if (!passed_initial_peak) {
						// For the temperature to drop below 1, the gap between requests
						// should be bigger than 1.
						if (age - prev_age > 1) {
							double prev_t = t * pow(temp_drop_alpha, age - 1 - prev_age);
							if (prev_t < become_cold_temp_threshold) {
								// t_at_time_prev_age * pow(temp_drop_alpha, age1 - 1 - prev_age) < become_cold_temp_threshold
								//
								// pow(temp_drop_alpha, age1 - 1 - prev_age) < become_cold_temp_threshold / t_at_time_prev_age
								// age1 - 1 - prev_age < log_(temp_drop_alpha) (become_cold_temp_threshold / t_at_time_prev_age)
								// age1 < log_(temp_drop_alpha) (become_cold_temp_threshold / t_at_time_prev_age) + 1 + prev_age
								//
								long age1 = int(log(become_cold_temp_threshold / t) / log(temp_drop_alpha) + 1 + prev_age);
								initial_hot_region_length_until_cold = age1;

								passed_initial_peak = true;
								// The obj becomes cold after the initial peak.
								break;
							}
						}
					}

					t = t * pow(temp_drop_alpha, age - prev_age) + cnt;
				}
				// 1. Calc initial-peak temprature
				if (!passed_initial_peak) {
					initial_hot_region_length_until_last_req = age;
				}

				//age_temp[age] = t;
				prev_age = age;
			}

			if (!passed_initial_peak) {
				long age1 = int(log(become_cold_temp_threshold / t) / log(temp_drop_alpha) + 1 + prev_age);
				initial_hot_region_length_until_cold = age1;
			}

			if ( (initial_hot_region_length_until_last_req <= -1)
					|| (initial_hot_region_length_until_cold <= -1)
					|| (initial_hot_region_length_until_last_req >= initial_hot_region_length_until_cold) )
				THROW("Unexpected");

			// Make the lengths start from 1s
			initial_hot_region_length_until_last_req ++;
			initial_hot_region_length_until_cold ++;
		}


		UtAgeCnts(const string& line) {
			vector<string> t;
			static const auto sep = boost::is_any_of(" ");
			boost::split(t, line, sep);
			if (t.size() % 2 == 0)
				THROW(boost::format("Unexpected %d") % t.size());
			last_update_time = t[0];

			for (size_t i = 1; i < t.size(); i += 2) {
				long age = atol(t[i].c_str());
				int cnt = atoi(t[i + 1].c_str());
				age_cnt[age] = cnt;
			}
			// age_cnt().size() > 0. The data files don't have (obj, last_ut) with 0
			// read after an upate.

			_CalcTempByAge();
		}
	};


	vector<long> _initial_hot_region_length_until_last_req;
	vector<long> _initial_hot_region_length_until_cold;
	mutex _lock;

	void MergeTemperatures(const map<long, vector<UtAgeCnts*> >& oid_u_ac) {
		std::lock_guard<std::mutex> _(_lock);
		
		for (auto i: oid_u_ac)
			for (auto j: i.second) {
				_initial_hot_region_length_until_last_req.push_back(j->initial_hot_region_length_until_last_req);
				_initial_hot_region_length_until_cold.push_back(j->initial_hot_region_length_until_cold);
			}
	}


	void ReadFile() {
		while (true) {
			boost::timer::cpu_timer tmr;

			string fn;
			try {
				fn = _q.Pop();
			} catch (const ConQEmpty& e) {
				break;
			}

			std::ifstream ifs(fn);
			//Cons::P(boost::format("Reading file %s ...") % fn);
			static const auto sep = boost::is_any_of(" ");
			long oid = -1;
			string line;
			bool done_with_file = false;

			map<long, vector<UtAgeCnts*> > oid_u_ac;
			while (true) {
				if (oid != -1)
					THROW("Unexpected");

				if (! getline(ifs, line))
					THROW("Unexpected");
				oid = atol(line.c_str());
				//Cons::P(boost::format("oid=%d") % oid);

				int num_read_groups = 0;
				while (true) {
					if (! getline(ifs, line)) {
						if (num_read_groups == 0)
							THROW("Unexpected");
						else {
							done_with_file = true;
							break;
						}
					}

					if (line.size() == 0) {
						// Done with this obj
						oid = -1;
						break;
					}

					// Process a read group
					auto it = oid_u_ac.find(oid);
					if (it == oid_u_ac.end())
						oid_u_ac[oid] = vector<UtAgeCnts*>();
					oid_u_ac[oid].push_back(new UtAgeCnts(line));
					num_read_groups ++;
				}

				if (done_with_file)
					break;
			}

			int num_objut = 0;
			for (auto i: oid_u_ac)
				num_objut += i.second.size();

			Cons::P(boost::format(
						"Analyzed %s in %.0f ms\n"
						"  %d objs\n"
						"  number of (obj, last_update_time)s: %d\n")
					% fn % (tmr.elapsed().wall / 1000000.0)
					% oid_u_ac.size()
					% num_objut
					);

			MergeTemperatures(oid_u_ac);

			// Free the memory
			for (auto i: oid_u_ac)
				for (auto j: i.second)
					delete j;
		}
	}

	void GenStat() {
		vector<string> fns = Util::ListDir(boost::regex_replace(Conf::GetStr("in_dir"),
					boost::regex("~"), Util::HomeDir()));
		int i = 0;
		boost::regex e(".+/\\d\\d\\d$");
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
				if (i == 3) {
					Cons::P(boost::format("Loaded %d for debugging") % i);
					break;
				}
			}
		}
		Cons::P(boost::format("Found %d input files") % _q.Size());

 		int num_threads = thread::hardware_concurrency();
 		Cons::P(boost::format("Found %d CPUs") % num_threads);

		{
			Cons::MT _("Calaulating initial max temperature ...");
			vector<thread> threads;
			for (int i = 0; i < num_threads; i ++)
				threads.push_back(thread(ReadFile));
			for (auto& t: threads)
				t.join();
		}
		{
			Cons::MT _("Generating stat and creating CDF files ...");
			{
				string fn = str(boost::format("%s/initial-hot-region-length-until-last_req") % _dn_out);
				ofstream ofs(fn);
				if (! ofs.is_open())
					THROW(boost::format("Unable to open file %s") % fn);
				Stat::GenCDF<long>(_initial_hot_region_length_until_last_req, ofs);
				ofs.close();
				Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
			}
			{
				string fn = str(boost::format("%s/initial-hot-region-length-until-cold") % _dn_out);
				ofstream ofs(fn);
				if (! ofs.is_open())
					THROW(boost::format("Unable to open file %s") % fn);
				Stat::GenCDF<long>(_initial_hot_region_length_until_cold, ofs);
				ofs.close();
				Cons::P(boost::format("created %s %d") % fn % boost::filesystem::file_size(fn));
			}
		}
	}
};


int main(int argc, char* argv[]) {
	try {
		signal(SIGSEGV, on_signal);
		signal(SIGINT, on_signal);

		Conf::Init(argc, argv);

		_dn_out = boost::regex_replace(Conf::GetStr("dn_out"),
				boost::regex("~"), Util::HomeDir());
		boost::filesystem::create_directories(_dn_out);

		Parallel::GenStat();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
