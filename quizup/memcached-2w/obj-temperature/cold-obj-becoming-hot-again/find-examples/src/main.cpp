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
		map<long, double> age_temp;

		// Finding a good example with 2 peaks. 3 is distracting. Ideally with
		// reads lasting for quite a while after the second peak, cause those are
		// what are gonna benefit from the record re-insertions.

		// First peak in 5 mins
		bool first_peak = false;

		// Become cold before the last read
		bool become_cold = false;

		bool become_hot_again = false;

		bool good_example = false;

		// File 707
		// Obj ID: 707071048856088133
		// 160719-212701.546936

		// File 269
		// Obj ID: 269696808497106387
		// 160720-031222.361281

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
					if (first_peak && !become_cold) {
						// For the temperature to drop below 1, the gap between requests
						// should be bigger than 1.
						if (age - prev_age > 1) {
							double prev_t = t * pow(temp_drop_alpha, age - 1 - prev_age);
							if (prev_t < become_cold_temp_threshold) {
								become_cold = true;
							}
						}
					}

					t = t * pow(temp_drop_alpha, age - prev_age) + cnt;

					// 1. Check a first peak in the first 5 mins
					if (! first_peak) {
						if (age < 5 && t > 70) {
							first_peak = true;
						}
					}

					// 3. Check if the temperature rises again
					if (become_cold && !become_hot_again) {
						if ((10 * 60 < age && age < 14 * 60) && (t > 50)) {
							become_hot_again = true;
							good_example = true;
						}
					}
				}

				age_temp[age] = t;
				prev_age = age;
			}
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

			_CalcTempByAge();
		}
	};

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

			// Generate temperature by age per object and last update time. Output
			// cold-become-hot objects only.
			{
				// Number of (obj, last_update_time)s that become cold and hot
				int num_objut = 0;
				int num_good_examples = 0;
				for (auto i: oid_u_ac) {
					for (auto j: i.second) {
						num_objut ++;
						if (j->good_example)
							num_good_examples ++;
					}
				}

				if (num_good_examples > 0) {
					string fn_out = str(boost::format("%s/%s") % _dn_out % fn.substr(fn.size() - 3));
					ofstream ofs(fn_out);
					if (! ofs.is_open())
						THROW(boost::format("Unable to open file %s") % fn_out);

					ofs << boost::format("# number of (obj, last_update_time)s: %d\n") % num_objut;
					ofs << boost::format("# number of good example hot-cold-hot (obj, last_update_time)s: %d %.2f%%\n")
							% num_good_examples
							% (100.0 * num_good_examples / num_objut);

					for (auto i: oid_u_ac) {
						bool good_example = false;
						for (auto j: i.second) {
							if (j->good_example) {
								good_example = true;
								break;
							}
						}
						if (! good_example)
							continue;

						long oid = i.first;
						ofs << boost::format("# %d\n") % oid;
						for (auto j: i.second) {
							if (! j->good_example)
								continue;
							ofs << boost::format("# %s\n") % j->last_update_time;

							long age_prev = -1;
							long age_now = -1;
							double temp_prev = -1.0;

							for (auto k: j->age_temp) {
								long age0 = k.first;
								double temp0 = k.second;

								if (age_now != -1) {
									while (age_now < age0) {
										ofs << boost::format("%d - %.3f\n") % age_now
											% (temp_prev * pow(temp_drop_alpha, age_now - age_prev));
										age_now ++;
									}
								}

								ofs << boost::format("%d %d %.3f\n") % age0 % (j->age_cnt[age0]) % temp0;
								age_prev = age0;
								temp_prev = temp0;
								age_now = age0 + 1;
							}

							if (age_now != -1) {
								while (true) {
									double t = temp_prev * pow(temp_drop_alpha, age_now - age_prev);
									ofs << boost::format("%d - %.3f\n") % age_now % t;
									if (t < become_cold_temp_threshold)
										break;
									age_now ++;
								}
							}

							ofs << "\n";
						}
					}
					ofs.close();

					Cons::P(boost::format(
								"Analyzed %s in %.0f ms\n"
								"  loaded %d objs\n"
								"  created %s %d\n"
								"    number of (obj, last_update_time)s: %d\n"
								"    number of good hot-cold-hot example (obj, last_update_time)s: %d %.2f%%")
							% fn % (tmr.elapsed().wall / 1000000.0) % oid_u_ac.size()
							% fn_out % boost::filesystem::file_size(fn_out)
							% num_objut
							% num_good_examples
							% (100.0 * num_good_examples / num_objut)
							);
				} else {
					Cons::P(boost::format(
								"Analyzed %s in %.0f ms\n"
								"  loaded %d objs\n"
								"  No good examples here")
							% fn % (tmr.elapsed().wall / 1000000.0) % oid_u_ac.size()
							);
				}

				// Free the memory
				for (auto i: oid_u_ac)
					for (auto j: i.second)
						delete j;
			}
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
				if (i == 5) {
					Cons::P(boost::format("Loaded %d for debugging") % i);
					break;
				}
			}
		}

		Cons::P(boost::format("Found %d input files") % _q.Size());

 		int num_threads = thread::hardware_concurrency();
 		Cons::P(boost::format("Found %d CPUs") % num_threads);

 		vector<thread> threads;
 		for (int i = 0; i < num_threads; i ++)
 			threads.push_back(thread(ReadFile));
 		for (auto& t: threads)
 			t.join();
	}
};


int main(int argc, char* argv[]) {
	try {
		signal(SIGSEGV, on_signal);
		signal(SIGINT, on_signal);

		Conf::Init(argc, argv);

		_dn_out = boost::regex_replace(Conf::GetStr("out_dir"),
					boost::regex("~"), Util::HomeDir());
		boost::filesystem::create_directories(_dn_out);

		//Serial::GenStat();
		Parallel::GenStat();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
