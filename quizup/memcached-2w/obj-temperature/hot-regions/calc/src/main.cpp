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

string _fn_out;


void on_signal(int sig) {
	cout << boost::format("\nGot a signal: %d\n%s\n") % sig % Util::Indent(Util::StackTrace(1), 2);
  exit(1);
}


struct HotRegion {
	// Inactivity time window length in minutes before this hot region.
	//   2^31 is big enough to cover 4085 years.
	int inactivity_window_length;
	int age_begin;
	int num_reads;
	int max_temperature;
	// The length of time in minutes of this region
	int length;

	HotRegion(
		int inactivity_window_length_,
		int age_begin_,
		int num_reads_,
		int max_temperature_,
		int length_)
	: inactivity_window_length(inactivity_window_length_),
		age_begin(age_begin_),
		num_reads(num_reads_),
		max_temperature(max_temperature_),
		length(length_)
	{
		if (inactivity_window_length < 0)
			THROW("Unexpected");

		if (age_begin < 0)
			THROW("Unexpected");

		if (num_reads <= 0)
			THROW("Unexpected");

		if (max_temperature <= 0.0)
			THROW("Unexpected");

		// Temp 1 drops to 0.001 in 67 mins
		if (length <= 65)
			THROW("Unexpected");
	}
};


namespace Parallel {
	ConcurrentQ<string> _q;

	// Calculate temperature by time with exponential smoothing.
	//   https://en.wikipedia.org/wiki/Exponential_smoothing
	//
	// temp_drop_alpha: temperature drop smoothing factor. Temperature decays by 0.9 every
	// minute. Seems like a reasonable one. Temp 1 drops to 0.001 in 65 mins,
	// about 1.5 hours.
	const double temp_drop_alpha = 0.9;

	// Temp 1 drops to 0.001 in 65 mins, about 1 hour.
	const double become_cold_temp_threshold = 0.001;

	struct UtAccFreqByAge {
		string last_update_time;
		// map< age, cnt >
		map<long, int> age_cnt;

		// Not need for now. Maybe later for plotting.
		// map<long, double> age_temp;

		vector<HotRegion> hot_regions;

		void _CalcHotRegionsByAge() {
			// t: current temperature
			double t = 0.0;
			long prev_age = -1;

			// Age of the end of the prev hot region
			long age_prev_hot_region_end = 0;

			// In the current hot region
			int num_reads = 0;
			double max_temp_in_hot_region = 0.0;
			long age_cur_hot_region_begin = -1;

			long inactivity_time_window_length_before_cur_hot_region = 0;

			//string fmt = "%5d %5d %5d %5d";
			//Cons::P(Util::BuildHeader(fmt, "age_hot_region_begin age_hot_region_end hot_region_length num_reads"));

			for (auto i: age_cnt) {
				long age = i.first;
				int cnt = i.second;

				if (prev_age == -1) {
					t = cnt * (1.0 / (1.0 - temp_drop_alpha));
				} else {
					// Check if the temperature drops
					//
					// For the temperature to drop below 1, the gap between requests
					// should be bigger than 1.
					if (age - prev_age > 1) {
						// Temperature at (age - 1)
						double t_at_age_1 = t * pow(temp_drop_alpha, (age - 1) - prev_age);
						if (t_at_age_1 < become_cold_temp_threshold) {
							// It became cold at age age1 (age_cur_hot_region_end):
							//   prev_t * pow(temp_drop_alpha, (age1 - 1) - prev_age) < become_cold_temp_threshold
							//
							//   pow(temp_drop_alpha, age1 - 1 - prev_age) < become_cold_temp_threshold / prev_t
							//   age1 - 1 - prev_age < log_(temp_drop_alpha) (become_cold_temp_threshold / prev_t)
							//   age1 < log_(temp_drop_alpha) (become_cold_temp_threshold / prev_t) + 1 + prev_age
							//
							long age_cur_hot_region_end = long(log(become_cold_temp_threshold / t) / log(temp_drop_alpha) + 1 + prev_age);
							long hot_region_length = age_cur_hot_region_end - age_cur_hot_region_begin;
							//Cons::P(boost::format(fmt) % age_cur_hot_region_begin % age_cur_hot_region_end % hot_region_length % num_reads);

							// Detected a temperature drop, the end of the previous hot region.
							hot_regions.push_back(
									HotRegion(inactivity_time_window_length_before_cur_hot_region,
										age_cur_hot_region_begin,
										num_reads,
										max_temp_in_hot_region,
										hot_region_length));

							// Reset stat
							num_reads = 0;
							max_temp_in_hot_region = 0.0;
							age_cur_hot_region_begin = -1;

							age_prev_hot_region_end = age_cur_hot_region_end;
						}
					}

					t = t * pow(temp_drop_alpha, age - prev_age) + cnt;
				}

				num_reads += cnt;
				max_temp_in_hot_region = max(t, max_temp_in_hot_region);

				if (age_cur_hot_region_begin == -1) {
					age_cur_hot_region_begin = age;
					inactivity_time_window_length_before_cur_hot_region = age - age_prev_hot_region_end;
				}

				//age_temp[age] = t;
				prev_age = age;
			}

			// It became cold at age age1 (age_cur_hot_region_end):
			//   prev_t * pow(temp_drop_alpha, (age1 - 1) - prev_age) < become_cold_temp_threshold
			//
			//   pow(temp_drop_alpha, age1 - 1 - prev_age) < become_cold_temp_threshold / prev_t
			//   age1 - 1 - prev_age < log_(temp_drop_alpha) (become_cold_temp_threshold / prev_t)
			//   age1 < log_(temp_drop_alpha) (become_cold_temp_threshold / prev_t) + 1 + prev_age
			//
			long age_cur_hot_region_end = long(log(become_cold_temp_threshold / t) / log(temp_drop_alpha) + 1 + prev_age);
			long hot_region_length = age_cur_hot_region_end - age_cur_hot_region_begin;
			//Cons::P(boost::format(fmt) % age_cur_hot_region_begin % age_cur_hot_region_end % hot_region_length % num_reads);

			// Add the last hot region
			hot_regions.push_back(
					HotRegion(inactivity_time_window_length_before_cur_hot_region,
						age_cur_hot_region_begin,
						num_reads,
						max_temp_in_hot_region,
						hot_region_length));
		}


		UtAccFreqByAge(const string& line) {
			vector<string> t;
			static const auto sep = boost::is_any_of(" ");
			boost::split(t, line, sep);
			if (t.size() % 2 == 0)
				THROW(boost::format("Unexpected %d") % t.size());
			last_update_time = t[0];
			//Cons::P(boost::format("last_update_time=%s") % last_update_time);

			for (size_t i = 1; i < t.size(); i += 2) {
				long age = atol(t[i].c_str());
				int cnt = atoi(t[i + 1].c_str());
				age_cnt[age] = cnt;
			}

			_CalcHotRegionsByAge();
		}
	};


	// vector<hot_region_order, HotRegion>
	map<int, vector<HotRegion> > _hot_regions;
	mutex _lock;

	void MergeStat(const map<long, vector<UtAccFreqByAge*> >& oid_u_ac) {
		std::lock_guard<std::mutex> _(_lock);
		for (auto i: oid_u_ac) {
			for (auto j: i.second) {
				int order = 0;
				for (const auto& k: j->hot_regions) {
					auto it = _hot_regions.find(order);
					if (it == _hot_regions.end())
						_hot_regions[order] = vector<HotRegion>();
					_hot_regions[order].push_back(k);
					order ++;
				}
			}
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

			map<long, vector<UtAccFreqByAge*> > oid_u_ac;
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
						oid_u_ac[oid] = vector<UtAccFreqByAge*>();
					oid_u_ac[oid].push_back(new UtAccFreqByAge(line));
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

			MergeStat(oid_u_ac);

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
			Cons::MT _("Calculating hot regions ...");
			vector<thread> threads;
			for (int i = 0; i < num_threads; i ++)
				threads.push_back(thread(ReadFile));
			for (auto& t: threads)
				t.join();
		}

		{
			Cons::MT _("Generating stat ...");

			long sum_num_reads = 0;
			for (auto i: _hot_regions)
				for (const auto& hr: i.second)
					sum_num_reads += hr.num_reads;

			ofstream ofs(_fn_out);
			if (! ofs.is_open())
				THROW(boost::format("Unable to open file %s") % _fn_out);

			ofs << boost::format("# Total num reads: %d\n") % sum_num_reads;
			ofs << "#\n";

			string fmt = "%2d %8d %10d %7.4f"
				" %8.3f %7.3f"
				" %8.3f %7.3f %6.2f";
			ofs << Util::BuildHeader(fmt,
					"order num_hot_regions num_reads num_reads_percent"
					" avg_inactivity_window_length_before num_reads_per_region"
					" avg_hot_region_start_age avg_hot_region_length avg_max_temp"
					) << "\n";

			for (auto i: _hot_regions) {
				int order = i.first;
				//const auto& hrs = i.second;

				long sum_inactivity_window_length = 0;
				long sum_age_begin = 0 ;
				long num_reads = 0;
				double sum_max_temp = 0.0;
				long sum_length = 0;
				for (const auto& hr: i.second) {
					sum_inactivity_window_length += hr.inactivity_window_length;
					sum_age_begin += hr.age_begin;
					num_reads += hr.num_reads;
					sum_max_temp += hr.max_temperature;
					sum_length += hr.length;
				}
				double avg_max_temp = sum_max_temp / i.second.size();

				ofs << (boost::format(fmt)
						% order % i.second.size()
						% num_reads % (100.0 * num_reads / sum_num_reads)

						% (1.0 * sum_inactivity_window_length / i.second.size())
						% (1.0 * num_reads / i.second.size())

						% (1.0 * sum_age_begin / i.second.size())
						% (1.0 * sum_length / i.second.size())
						% avg_max_temp) << "\n";
			}
			ofs.close();
			Cons::P(boost::format("created %s %d") % _fn_out % boost::filesystem::file_size(_fn_out));
		}
	}
};

// Output:
// Aggregate stat for
// - 1st hot region
//   - Inactivity window before this hot region in minutes
//   - Number of reads
//   - Max temperature
//   - Region length in minutes
// - 2nd hot region
//   - Ths same

int main(int argc, char* argv[]) {
	try {
		signal(SIGSEGV, on_signal);
		signal(SIGINT, on_signal);

		Conf::Init(argc, argv);

		_fn_out = boost::regex_replace(Conf::GetStr("fn_out"),
				boost::regex("~"), Util::HomeDir());

		string dn_out = boost::filesystem::path(_fn_out).parent_path().string();
		boost::filesystem::create_directories(dn_out);

		Parallel::GenStat();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
