#include <condition_variable>
#include <thread>
#include <boost/algorithm/string.hpp>

#include "conf.h"
#include "cons.h"
#include "prog-mon.h"
#include "simtime.h"
#include "util.h"

using namespace std;


namespace ProgMon {

struct Stat {
	size_t cnt = 0;
	long sum = 0;
	double avg = 0.0;
	long max = 0;
	map<double, long> tail;
};


string _fn_client_log;

size_t _total_num_ops = 0;

thread _t;

bool _reporter_stop = false;
mutex _reporter_stop_mutex;
condition_variable _reporter_stop_cv;


std::mutex _mutex_running_on_time;
long _running_on_time_cnt = 0;

std::mutex _mutex_running_behind;
long _running_behind_cnt = 0;
long _running_behind_dur = 0;

std::mutex _mutex_latency_put;
std::vector<long> _latency_put;

std::mutex _mutex_latency_get;
std::vector<long> _latency_get;


long _total_put_cnt = 0;
long _total_get_cnt = 0;


void ReporterThread();
void _ReporterThread();
void _ReportPerSecStat(ofstream& ofs, const string& fmt1, const string& fmt2);
void _GetAndReset(
		long& running_on_time_cnt,
		long& running_behind_cnt,
		long& running_behind_dur,
		vector<long>& latency_put,
		vector<long>& latency_get);
Stat GenStat(vector<long>& v);


// This is called while a lock is held.
void IncTotalNumOps(size_t s) {
	_total_num_ops += s;
}


vector<WorkerStat*> _worker_stat;
mutex _worker_stat_mutex;
WorkerStat* GetWorkerStat() {
	WorkerStat* ws = new WorkerStat();
	{
		lock_guard<mutex> _(_worker_stat_mutex);
		_worker_stat.push_back(ws);
	}
	return ws;
}


void ReporterStart() {
	_t = thread(ReporterThread);
}


void ReporterStop() {
	// Tell the reporter thread to stop
	{
		unique_lock<mutex> _(_reporter_stop_mutex);
		_reporter_stop = true;
	}
	_reporter_stop_cv.notify_one();

	// Wait for the thread to finish
	_t.join();

	{
		lock_guard<mutex> _(_worker_stat_mutex);
		for (auto& ws: _worker_stat)
			delete ws;
		_worker_stat.clear();
	}
}


void ReporterThread() {
	try {
		_ReporterThread();
	} catch (const exception& e) {
		Cons::P(boost::format("Got an exception: %s") % e.what());
		exit(1);
	}
}


void _ReporterThread() {
	string fmt1 =
		"%12d"
		// 161216-231802.611
		// 01234567890123456
		" %6.2f"
		" %17s %17s"
		" %6d %7d %6.0f"

		" %7d %7.0f"
		" %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f"

		" %7d %7.0f"
		" %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f %9.0f"
		;
	string header1 = Util::BuildHeader(fmt1,
				"since_simulation_time_begin"
				" progress(percent)"
				" simulation_time(wall_clock) simulated_time"
				" running_on_time running_behind avg_runing_behind_dur_avg_in_ms"
				" puts latency_put_avg_in_us"

				" latency_put_99p_in_us"
				" latency_put_99.1p_in_us"
				" latency_put_99.2p_in_us"
				" latency_put_99.3p_in_us"
				" latency_put_99.4p_in_us"
				" latency_put_99.5p_in_us"
				" latency_put_99.6p_in_us"
				" latency_put_99.7p_in_us"
				" latency_put_99.8p_in_us"
				" latency_put_99.9p_in_us"
				" latency_put_99.91p_in_us"
				" latency_put_99.92p_in_us"
				" latency_put_99.93p_in_us"
				" latency_put_99.94p_in_us"
				" latency_put_99.95p_in_us"
				" latency_put_99.96p_in_us"
				" latency_put_99.97p_in_us"
				" latency_put_99.98p_in_us"
				" latency_put_99.99p_in_us"

				" gets latency_get_avg_in_us"

				" latency_get_99p_in_us"
				" latency_get_99.1p_in_us"
				" latency_get_99.2p_in_us"
				" latency_get_99.3p_in_us"
				" latency_get_99.4p_in_us"
				" latency_get_99.5p_in_us"
				" latency_get_99.6p_in_us"
				" latency_get_99.7p_in_us"
				" latency_get_99.8p_in_us"
				" latency_get_99.9p_in_us"
				" latency_get_99.91p_in_us"
				" latency_get_99.92p_in_us"
				" latency_get_99.93p_in_us"
				" latency_get_99.94p_in_us"
				" latency_get_99.95p_in_us"
				" latency_get_99.96p_in_us"
				" latency_get_99.97p_in_us"
				" latency_get_99.98p_in_us"
				" latency_get_99.99p_in_us"
				);

	string fmt2 =
		"%12d"
		" %6.2f"
		" %17s %17s"
		" %7d %8.0f"
		" %7d %7.0f"
		" %9.0f %9.0f %9.0f %9.0f %9.0f"
		;
	string header2 = Util::BuildHeader(fmt2,
				"since_simulation_time_begin"
				" progress(percent)"
				" simulation_time(wall_clock) simulated_time"
				" puts latency_put_avg_in_us"
				" gets latency_get_avg_in_us"
				" latency_get_99p_in_us"
				" latency_get_99.5p_in_us"
				" latency_get_99.9p_in_us"
				" latency_get_99.95p_in_us"
				" latency_get_99.99p_in_us"
				);

	string dn = str(boost::format("%s/%s")
			% Util::SrcDir()
			% Conf::GetStr("progress_log_dn"));
	boost::filesystem::create_directories(dn);

	_fn_client_log = str(boost::format("%s/quizup-client-log-%s") % dn % Util::ToString(SimTime::SimulationTimeBegin()));
	ofstream ofs(_fn_client_log);
	ofs << Util::Prepend("# ", Conf::Desc());
	ofs << "#\n";
	ofs << boost::format("# hostname: %s\n") % Util::Hostname();
	ofs << boost::format("# simulation_time_begin: %s\n") % Util::ToString(SimTime::SimulationTimeBegin());
	ofs << boost::format("# simulation_time_end  : %s\n") % Util::ToString(SimTime::SimulationTimeEnd());
	ofs << boost::format("# simulated_time_begin : %s\n") % Util::ToString(SimTime::SimulatedTimeBegin());
	ofs << boost::format("# simulated_time_end   : %s\n") % Util::ToString(SimTime::SimulatedTimeEnd());
	ofs << "#\n";

	for (int i = 0; !_reporter_stop; i ++) {
		if (i % 30 == 0) {
			ofs << header1 << "\n";
			Cons::P(header2);
		}

		{
			unique_lock<mutex> lk(_reporter_stop_mutex);
			_reporter_stop_cv.wait_for(lk, chrono::milliseconds(1000),
					[](){return _reporter_stop;});
		}

		if (_reporter_stop) {
			_ReportPerSecStat(ofs, fmt1, fmt2);

			// Report overall stat
			auto s1 = boost::format("# %d / %d operations requested. %d puts, %d gets.")
					% (_total_put_cnt + _total_get_cnt) % _total_num_ops
					% _total_put_cnt % _total_get_cnt
					;
			ofs << s1 << "\n";
			Cons::P(s1);
			break;
		} else {
			_ReportPerSecStat(ofs, fmt1, fmt2);
		}
	}

	ofs.close();
	Cons::P(boost::format("Created %s %d") % _fn_client_log % boost::filesystem::file_size(_fn_client_log));
}


void _ReportPerSecStat(ofstream& ofs, const string& fmt1, const string& fmt2) {
	boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
	string lap_time;
	{
		string s = boost::posix_time::to_simple_string(now - SimTime::SimulationTimeBegin());
		vector<string> t;
		static const auto sep = boost::is_any_of(".");
		boost::split(t, s, sep);
		if (t.size() == 2) {
			lap_time = t[0] + "." + t[1].substr(0, 3);
		} else {
			// Sometimes s doesn't have a dot in it. Interesting.
			lap_time = s;
		}
	}

	// Get-and-reset statistics
	long running_on_time_cnt = 0;
	long running_behind_cnt = 0;
	long running_behind_dur = 0;
	vector<long> latency_put;
	vector<long> latency_get;
	{
		lock_guard<mutex> _(_worker_stat_mutex);
		for (auto& ws: _worker_stat)
			ws->GetAndReset(running_on_time_cnt,
					running_behind_cnt,
					running_behind_dur,
					latency_put,
					latency_get
					);
	}

	Stat latency_put_stat = GenStat(latency_put);
	Stat latency_get_stat = GenStat(latency_get);

	_total_put_cnt += latency_put_stat.cnt;
	_total_get_cnt += latency_get_stat.cnt;

	string cur_dt_str = Util::CurDateTimeStr();
	string now_simulated_time_str = Util::ToString(SimTime::ToSimulatedTime(now));

	auto s1 = boost::format(fmt1)
		% lap_time
		% (100.0 * (_total_put_cnt + _total_get_cnt) / _total_num_ops)
		% cur_dt_str
		% now_simulated_time_str
		% running_on_time_cnt
		% running_behind_cnt
		% (running_behind_cnt == 0 ? 0 : (0.001 * running_behind_dur / running_behind_cnt))
		% latency_put_stat.cnt
		% latency_put_stat.avg
		% latency_put_stat.tail[0.99]
		% latency_put_stat.tail[0.991]
		% latency_put_stat.tail[0.992]
		% latency_put_stat.tail[0.993]
		% latency_put_stat.tail[0.994]
		% latency_put_stat.tail[0.995]
		% latency_put_stat.tail[0.996]
		% latency_put_stat.tail[0.997]
		% latency_put_stat.tail[0.998]
		% latency_put_stat.tail[0.999]
		% latency_put_stat.tail[0.9991]
		% latency_put_stat.tail[0.9992]
		% latency_put_stat.tail[0.9993]
		% latency_put_stat.tail[0.9994]
		% latency_put_stat.tail[0.9995]
		% latency_put_stat.tail[0.9996]
		% latency_put_stat.tail[0.9997]
		% latency_put_stat.tail[0.9998]
		% latency_put_stat.tail[0.9999]
		% latency_get_stat.cnt
		% latency_get_stat.avg
		% latency_get_stat.tail[0.99]
		% latency_get_stat.tail[0.991]
		% latency_get_stat.tail[0.992]
		% latency_get_stat.tail[0.993]
		% latency_get_stat.tail[0.994]
		% latency_get_stat.tail[0.995]
		% latency_get_stat.tail[0.996]
		% latency_get_stat.tail[0.997]
		% latency_get_stat.tail[0.998]
		% latency_get_stat.tail[0.999]
		% latency_get_stat.tail[0.9991]
		% latency_get_stat.tail[0.9992]
		% latency_get_stat.tail[0.9993]
		% latency_get_stat.tail[0.9994]
		% latency_get_stat.tail[0.9995]
		% latency_get_stat.tail[0.9996]
		% latency_get_stat.tail[0.9997]
		% latency_get_stat.tail[0.9998]
		% latency_get_stat.tail[0.9999]
		;
	auto s2 = boost::format(fmt2)
		% lap_time
		% (100.0 * (_total_put_cnt + _total_get_cnt) / _total_num_ops)
		% cur_dt_str
		% now_simulated_time_str
		% latency_put_stat.cnt % latency_put_stat.avg
		% latency_get_stat.cnt % latency_get_stat.avg
		% latency_get_stat.tail[0.99]
		% latency_get_stat.tail[0.995]
		% latency_get_stat.tail[0.999]
		% latency_get_stat.tail[0.9995]
		% latency_get_stat.tail[0.9999]
		;

	ofs << s1 << "\n";
	Cons::P(s2);
}


const string& FnClientLog() {
	return _fn_client_log;
}


void WorkerStat::RunningOnTime() {
	lock_guard<mutex> _(_mutex_running_on_time);
	_running_on_time_cnt ++;
}


void WorkerStat::RunningBehind(const boost::posix_time::time_duration& td) {
	lock_guard<mutex> _(_mutex_running_behind);
	// This is not likely to overflow
	_running_behind_cnt ++;
	_running_behind_dur += td.total_microseconds();
}


void WorkerStat::LatencyPut(const long d) {
	lock_guard<mutex> _(_mutex_latency_put);
	_latency_put.push_back(d);
}


void WorkerStat::LatencyGet(const long d) {
	lock_guard<mutex> _(_mutex_latency_get);
	_latency_get.push_back(d);
}


void WorkerStat::GetAndReset(
		long& running_on_time_cnt,
		long& running_behind_cnt,
		long& running_behind_dur,
		vector<long>& latency_put,
		vector<long>& latency_get) {
	{ lock_guard<mutex> _(_mutex_running_on_time);
		running_on_time_cnt += _running_on_time_cnt;
		_running_on_time_cnt = 0; }
	{ lock_guard<mutex> _(_mutex_running_behind);
		running_behind_cnt += _running_behind_cnt;
		running_behind_dur += _running_behind_dur;
		_running_behind_cnt = 0;
		_running_behind_dur = 0; }
	{ lock_guard<mutex> _(_mutex_latency_put);
		latency_put.insert(latency_put.end(), _latency_put.begin(), _latency_put.end());
		vector<long>().swap(_latency_put); }
	{ lock_guard<mutex> _(_mutex_latency_get);
		latency_get.insert(latency_get.end(), _latency_get.begin(), _latency_get.end());
		vector<long>().swap(_latency_get); }
}


int cmpfunc(const void * a, const void * b)
{
	return ( *(long*)a - *(long*)b );
}


Stat GenStat(vector<long>& v) {
	Stat s;

	s.cnt = v.size();

	s.sum = 0;
	for (auto i: v)
		s.sum += i;

	if (s.cnt > 0) {
		s.avg = double(s.sum) / s.cnt;
	} else {
		s.avg = 0.0;
	}

	if (s.cnt == 0)
		return s;

	if (true) {
		sort(v.begin(), v.end());
	} else {
		// This doesn't make any difference
		long* a = &v[0];
		qsort(a, v.size(), sizeof(long), cmpfunc);
	}

	s.max = v[s.cnt - 1];

	// 99.0 99.1 ... 99.9
	for (int i = 9900; i <= 9990; i += 10) {
		double percentile = i / 10000.0;
		size_t p1 = s.cnt * percentile;
		if (p1 == s.cnt) p1 --;
		s.tail[percentile] = v[p1];
	}

	// 99.91 ... 99.99
	for (int i = 9991; i <= 9999; i += 1) {
		double percentile = i / 10000.0;
		size_t p1 = s.cnt * percentile;
		if (p1 == s.cnt) p1 --;
		s.tail[percentile] = v[p1];
	}

	return s;
}

}
