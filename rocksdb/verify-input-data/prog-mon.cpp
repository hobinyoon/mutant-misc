#include <condition_variable>
#include <mutex>
#include <thread>
#include <boost/algorithm/string.hpp>

#include "conf.h"
#include "cons.h"
#include "prog-mon.h"
#include "simtime.h"
#include "util.h"

using namespace std;


namespace ProgMon {

size_t _total_num_ops = 0;

mutex _mutex_running_on_time;
long _running_on_time_cnt = 0;

mutex _mutex_running_behind;
long _running_behind_cnt = 0;
long _running_behind_dur = 0;

thread _t;

bool _reporter_stop = false;
mutex _reporter_stop_mutex;
condition_variable _reporter_stop_cv;

mutex _mutex_latency_put;
long _put_cnt = 0;
long _latency_put_sum = 0;

mutex _mutex_latency_get;
long _get_cnt = 0;
long _latency_get_sum = 0;

long _total_put_cnt = 0;
long _total_get_cnt = 0;


void ReporterThread();
void _ReporterThread();


// This is called while a lock is held.
void IncTotalNumOps(size_t s) {
	_total_num_ops += s;
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
	string fmt =
		"%12d"
		// 161216-231802.611
		// 01234567890123456
		" %6.2f"
		" %17s %17s"
		" %5d %7d %7.0f"
		" %7d %7d %10.0f %8.0f"
		;
	string header = Util::BuildHeader(fmt,
				"since_simulation_time_begin"
				" progress(percent)"
				" simulation_time(wall_clock) simulated_time"
				" running_on_time running_behind avg_runing_behind_dur_avg_in_ms"
				" puts gets avg_latency_put_in_ns avg_latency_get_in_ns"
				);

	string dn = str(boost::format("%s/%s")
			% Util::SrcDir()
			% Conf::GetStr("progress_log_dn"));
	boost::filesystem::create_directories(dn);

	string fn = str(boost::format("%s/quizup-client-log-%s") % dn % Util::ToString(SimTime::SimulationTimeBegin()));
	ofstream ofs(fn);
	ofs << Util::Prepend("# ", Conf::Desc()) << "\n";

	for (int i = 0; !_reporter_stop; i ++) {
		if (i % 50 == 0) {
			Cons::P(header);
			ofs << header << "\n";
		}

		{
			unique_lock<mutex> lk(_reporter_stop_mutex);
			_reporter_stop_cv.wait_for(lk, chrono::milliseconds(1000),
					[](){return _reporter_stop;});
		}

		boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
		string lap_time;
		{
			string s = boost::posix_time::to_simple_string(now - SimTime::SimulationTimeBegin());
			vector<string> t;
			static const auto sep = boost::is_any_of(".");
			boost::split(t, s, sep);
			if (t.size() != 2)
				THROW("Unexpected");
			lap_time = t[0] + "." + t[1].substr(0, 3);
			//lap_time = str(boost::format("%s.%s.%d") % t[0] % t[1].substr(0, 3) % i);
		}

		if (_reporter_stop) {
			// Report only if there is anything to report to avoid double reporting.
			// Don't need to reset since this is called after all worker threads are
			// done.

			_total_put_cnt += _put_cnt;
			_total_get_cnt += _get_cnt;

			boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
			auto s0 = boost::format(fmt)
					% lap_time
					% (100.0 * (_total_put_cnt + _total_get_cnt) / _total_num_ops)
					% Util::CurDateTimeStr()
					% Util::ToString(SimTime::ToSimulatedTime(now))
					% _running_on_time_cnt
					% _running_behind_cnt
					% (_running_behind_cnt == 0 ? 0 : (1.0 * _running_behind_dur / _running_behind_cnt))
					% _put_cnt
					% _get_cnt
					% (_put_cnt == 0 ? 0 : (_latency_put_sum / _put_cnt))
					% (_get_cnt == 0 ? 0 : (_latency_get_sum / _get_cnt))
					;
			Cons::P(s0);
			ofs << s0 << "\n";
			auto s1 = boost::format("# %d / %d operations requested. %d puts, %d gets.")
					% (_total_put_cnt + _total_get_cnt) % _total_num_ops
					% _total_put_cnt % _total_get_cnt
					;
			Cons::P(s1);
			ofs << s1 << "\n";
			break;
		} else {
			// Get-and-reset statistics
			long running_on_time_cnt;
			{
				lock_guard<mutex> _(_mutex_running_on_time);
				running_on_time_cnt = _running_on_time_cnt;
				_running_on_time_cnt = 0;
			}

			long running_behind_cnt;
			long running_behind_dur;
			{
				lock_guard<mutex> _(_mutex_running_behind);
				running_behind_cnt = _running_behind_cnt;
				running_behind_dur = _running_behind_dur;
				_running_behind_cnt = 0;
				_running_behind_dur = 0;
			}

			long put_cnt;
			long latency_put_sum;
			{
				lock_guard<mutex> _(_mutex_latency_put);
				put_cnt = _put_cnt;
				latency_put_sum = _latency_put_sum;
				_put_cnt = 0;
				_latency_put_sum = 0;
			}

			long get_cnt;
			long latency_get_sum;
			{
				lock_guard<mutex> _(_mutex_latency_get);
				get_cnt = _get_cnt;
				latency_get_sum = _latency_get_sum;
				_get_cnt = 0;
				_latency_get_sum = 0;
			}

			_total_put_cnt += put_cnt;
			_total_get_cnt += get_cnt;

			boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
			auto s0 = boost::format(fmt)
				% lap_time
				% (100.0 * (_total_put_cnt + _total_get_cnt) / _total_num_ops)
				% Util::CurDateTimeStr()
				% Util::ToString(SimTime::ToSimulatedTime(now))
				% running_on_time_cnt
				% running_behind_cnt
				% (running_behind_cnt == 0 ? 0 : (1.0 * running_behind_dur / running_behind_cnt))
				% put_cnt
				% get_cnt
				% (put_cnt == 0 ? 0 : (latency_put_sum / put_cnt))
				% (get_cnt == 0 ? 0 : (latency_get_sum / get_cnt))
				;
			Cons::P(s0);
			ofs << s0 << "\n";
		}
	}

	ofs.close();
	Cons::P(boost::format("Created %s %d") % fn % boost::filesystem::file_size(fn));
}


void RunningOnTime() {
	lock_guard<mutex> _(_mutex_running_on_time);
	_running_on_time_cnt ++;
}


void RunningBehind(const boost::posix_time::time_duration& td) {
	lock_guard<mutex> _(_mutex_running_behind);
	// This is not likely to overflow
	_running_behind_cnt ++;
	_running_behind_dur += td.total_milliseconds();
}


//void LatencyPut(const chrono::duration& d) {
void LatencyPut(const long d) {
	lock_guard<mutex> _(_mutex_latency_put);
	_put_cnt ++;
	_latency_put_sum += d;
}


void LatencyGet(const long d) {
	lock_guard<mutex> _(_mutex_latency_get);
	_get_cnt ++;
	_latency_get_sum += d;
}

}
