#include <condition_variable>
#include <mutex>
#include <thread>
#include <boost/thread/thread.hpp>

#include "conf.h"
#include "cons.h"
#include "simtime.h"
#include "util.h"

using namespace std;

namespace SimTime {

// With the 1-2-1x replay, you need
//   simulation_time_0: start of the simulation time, i.e., the workload from 0.899% is getting replayed. The replay speed is 1x.
//   simulation_time_1: start of the 2x replay. for the next 1% of the workload.
//   simulation_time_2: start of the next 1x replay.
//   simulation_time_3: end of the simulation time

boost::posix_time::ptime _simulation_time_0;
boost::posix_time::ptime _simulation_time_1;
boost::posix_time::ptime _simulation_time_2;
boost::posix_time::ptime _simulation_time_3;
boost::posix_time::ptime _simulated_time_0;
boost::posix_time::ptime _simulated_time_1;
boost::posix_time::ptime _simulated_time_2;
boost::posix_time::ptime _simulated_time_3;

long _simulated_time_begin_long;

mutex _stop_requested_mutex;
bool _stop_requested = false;
condition_variable _stop_requested_cv;

bool _start_from_defined;
double _start_from = 0.0;
bool _stop_at_defined;
double _stop_at = 1.0;
boost::posix_time::ptime _simulated_time_stop_at;

bool _121x_speed_replay = false;


void Init1() {
	Cons::MT _("Init SimTime 1 ...", false);

	_121x_speed_replay = Conf::Get("121x_speed_replay").as<bool>();
	_simulated_time_0 = Util::ToPtime(Conf::GetStr("simulated_time_begin"));
	_simulated_time_3 = Util::ToPtime(Conf::GetStr("simulated_time_end"));

	_start_from_defined = Conf::Get("workload_start_from").IsDefined()
		&& (Conf::Get("workload_start_from").as<double>() != -1.0);
	if (_start_from_defined) {
		_start_from = Conf::Get("workload_start_from").as<double>();
		// Can't assign directly to _simulated_time_0. It complicates the
		// calculation of _simulated_time_stop_at below.
		boost::posix_time::ptime b = _simulated_time_0
			+ boost::posix_time::time_duration(0, 0, 0, (_simulated_time_3 - _simulated_time_0).total_nanoseconds() / 1000.0 * _start_from);

		string s = Util::ToString(b);
		// 160711-170502.871
		// 01234567890123456
		//
		// 160711170502871000
		// 012345678901234567
		_simulated_time_begin_long =
				atol(s.substr( 0, 2).c_str()) * 10000000000000000L
			+ atol(s.substr( 2, 2).c_str()) *   100000000000000L
			+ atol(s.substr( 4, 2).c_str()) *     1000000000000L
			+ atol(s.substr( 7, 2).c_str()) *       10000000000L
			+ atol(s.substr( 9, 2).c_str()) *         100000000L
			+ atol(s.substr(11, 2).c_str()) *           1000000L
			+ atol(s.substr(14).c_str())    *              1000L;
	}
}

// Calculate simulation / simulated time.  Set the _simulation_time_0 0.01
// sec after now.
//
// Not sure how to construct a std::chrono::time_point from a string with
// microsecond resolution. Go with boost::ptime. Hope it's not too slow.
void Init2() {
	Cons::MT _("Init SimTime 2 ...", false);

	boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
	_simulation_time_0 = now + boost::posix_time::milliseconds(10);

	_simulation_time_3 = _simulation_time_0 + boost::posix_time::seconds(Conf::Get("simulation_time_dur_in_sec").as<int>());

	Cons::P(boost::format("simulation_time_0: %s") % Util::ToString(_simulation_time_0));
	Cons::P(boost::format("simulation_time_1: %s") % Util::ToString(_simulation_time_1));
	Cons::P(boost::format("simulation_time_2: %s") % Util::ToString(_simulation_time_2));
	Cons::P(boost::format("simulation_time_3: %s") % Util::ToString(_simulation_time_3));
	Cons::P(boost::format("simulated_time_0 : %s") % Util::ToString(_simulated_time_0));
	Cons::P(boost::format("simulated_time_1 : %s") % Util::ToString(_simulated_time_1));
	Cons::P(boost::format("simulated_time_2 : %s") % Util::ToString(_simulated_time_2));
	Cons::P(boost::format("simulated_time_3 : %s") % Util::ToString(_simulated_time_3));

	// workload_stop_at needs to be calculated before the simulated time interval is shrunk.
	_stop_at_defined = Conf::Get("workload_stop_at").IsDefined()
		&& (Conf::Get("workload_stop_at").as<double>() != -1.0);
	if (_stop_at_defined) {
		_stop_at = Conf::Get("workload_stop_at").as<double>();
		_simulated_time_stop_at = _simulated_time_0
			+ boost::posix_time::time_duration(0, 0, 0, (_simulated_time_3 - _simulated_time_0).total_nanoseconds() / 1000.0 * _stop_at);
	}

	if (_start_from_defined) {
		_simulated_time_0 = _simulated_time_0
			+ boost::posix_time::time_duration(0, 0, 0, (_simulated_time_3 - _simulated_time_0).total_nanoseconds() / 1000.0 * _start_from);
		_simulation_time_3 = _simulation_time_0 + boost::posix_time::seconds(double(Conf::Get("simulation_time_dur_in_sec").as<int>()) * (1.0 - _start_from));
	}

	if (_121x_speed_replay) {
		_simulation_time_1 = _simulation_time_0 + boost::posix_time::time_duration(0, 0, 0, (_simulation_time_3 - _simulation_time_0).total_nanoseconds() / 1000.0 * 0.10);
		_simulation_time_2 = _simulation_time_0 + boost::posix_time::time_duration(0, 0, 0, (_simulation_time_3 - _simulation_time_0).total_nanoseconds() / 1000.0 * 0.15);
		_simulation_time_3 = _simulation_time_0 + boost::posix_time::time_duration(0, 0, 0, (_simulation_time_3 - _simulation_time_0).total_nanoseconds() / 1000.0 * 0.95);

		_simulated_time_1 = _simulated_time_0 + boost::posix_time::time_duration(0, 0, 0, (_simulated_time_3 - _simulated_time_0).total_nanoseconds() / 1000.0 * 0.10);
		_simulated_time_2 = _simulated_time_0 + boost::posix_time::time_duration(0, 0, 0, (_simulated_time_3 - _simulated_time_0).total_nanoseconds() / 1000.0 * 0.20);
	}

	if (_stop_at_defined || _start_from_defined) {
		Cons::P("Adjusted time:");
		Cons::P(boost::format("simulation_time_0: %s") % Util::ToString(_simulation_time_0));
		Cons::P(boost::format("simulation_time_1: %s") % Util::ToString(_simulation_time_1));
		Cons::P(boost::format("simulation_time_2: %s") % Util::ToString(_simulation_time_2));
		Cons::P(boost::format("simulation_time_3: %s") % Util::ToString(_simulation_time_3));
		Cons::P(boost::format("simulated_time_0 : %s") % Util::ToString(_simulated_time_0));
		Cons::P(boost::format("simulated_time_1 : %s") % Util::ToString(_simulated_time_1));
		Cons::P(boost::format("simulated_time_2 : %s") % Util::ToString(_simulated_time_2));
		Cons::P(boost::format("simulated_time_3 : %s") % Util::ToString(_simulated_time_3));
		Cons::P(boost::format("simulated_time_stop_at: %s") % Util::ToString(_simulated_time_stop_at));
		Cons::P(boost::format("simulated_time_begin_long: %d") % _simulated_time_begin_long);
	}
}


boost::posix_time::ptime _InterpolateSimulationTime(
		const boost::posix_time::ptime& simulated0
		, const boost::posix_time::ptime& simulated1
		, const boost::posix_time::ptime& simulated
		, const boost::posix_time::ptime& simulation0
		, const boost::posix_time::ptime& simulation1) {
	// simulation0 : a (simulation, output) : simulation1
	// simulated0  : b (simulated, input)   : simulated1
	//
	// a - simulation0 : b - simulated0 = simulation1 - simulation0 : simulated1 - simulated0
	// a - simulation0 = (b - simulated0) * (simulation1 - simulation0) / (simulated1 - simulated0)
	// a = (b - simulated0) * (simulation1 - simulation0) / (simulated1 - simulated0) + simulation0
	auto td = boost::posix_time::time_duration(0, 0, 0,
			double((simulated - simulated0).total_nanoseconds())
			* double((simulation1 - simulation0).total_nanoseconds())
			/ double((simulated1 - simulated0).total_nanoseconds())
			/ 1000.0
			);
	return simulation0 + td;
}


boost::posix_time::ptime _InterpolateSimulatedTime(
		const boost::posix_time::ptime& simulated0
		, const boost::posix_time::ptime& simulated1
		, const boost::posix_time::ptime& simulation0
		, const boost::posix_time::ptime& simulation1
		, const boost::posix_time::ptime& simulation) {
	// simulation0 : a (ts_simulation, input) : simulation1
	// simulated0  : b (ts_simulated, output) : simulated1
	//
	// b - simulated0 = (a - simulation0) * (simulated1 - simulated0) / (simulation1 - simulation0)
	// b = (a - simulation0) * (simulated1 - simulated0) / (simulation1 - simulation0) + simulated0
	//
	// The default time_duration precision seems to be microsecond from an
	// experiment. Not sure how to change it. Might be a system-wide
	// configuration.
	//   boost::posix_time::time_duration td(0, 0, 0, 1);
	//   cout << td << "\n";
	auto td = boost::posix_time::time_duration(0, 0, 0,
				double((simulation - simulation0).total_nanoseconds())
				* double((simulated1 - simulated0).total_nanoseconds())
				/ double((simulation1 - simulation0).total_nanoseconds())
				/ 1000.0
				);
	return simulated0 + td;
}


void MaySleepUntilSimulatedTime(const boost::posix_time::ptime& ts_simulated, ProgMon::WorkerStat* ws) {
	// With a ns resolution, long can contain up to 292 years. Good enough.
	//   calc "(2^63 - 1) / (10^9) / 3600 / 24 / 365.25"
	//   = 292 years

	boost::posix_time::ptime ts_simulation;
	if (_121x_speed_replay) {
		// _simulation_time_0 : _simulation_time_1 : _simulation_time_2 : _simulation_time_3
		//  _simulated_time_0 :  _simulated_time_1 :  _simulated_time_2 :  _simulated_time_3
		//
		// Figure out a given b
		//   b (ts_simulated, input)
		//   a (ts_simulation, output)
		if (ts_simulated < _simulated_time_0) {
			THROW("Unexpected");
		} else if (ts_simulated < _simulated_time_1) {
			ts_simulation = _InterpolateSimulationTime(_simulated_time_0, _simulated_time_1, ts_simulated, _simulation_time_0, _simulation_time_1);
		} else if (ts_simulated < _simulated_time_2) {
			ts_simulation = _InterpolateSimulationTime(_simulated_time_1, _simulated_time_2, ts_simulated, _simulation_time_1, _simulation_time_2);
		} else if (ts_simulated <= _simulated_time_3) {
			ts_simulation = _InterpolateSimulationTime(_simulated_time_2, _simulated_time_3, ts_simulated, _simulation_time_2, _simulation_time_3);
		} else {
			// This can happen when the system is saturated
			//THROW(boost::format("Unexpected: simulated_3=%s simulated=%s") % Util::ToString(_simulated_time_3) % Util::ToString(_simulated_time_3));
		}
	} else {
		ts_simulation = _InterpolateSimulationTime(_simulated_time_0, _simulated_time_3, ts_simulated, _simulation_time_0, _simulation_time_3);
	}

	boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
	if (now < ts_simulation) {
		auto sleep_dur = (ts_simulation - now).total_nanoseconds();
		{
			// I'm hoping this is reentrant by multiple worker threads. Looks like, because wait_for() unlocks the mutex.
			unique_lock<mutex> lk(_stop_requested_mutex);
			_stop_requested_cv.wait_for(lk, chrono::nanoseconds(sleep_dur), [](){return _stop_requested;});
		}

		ws->RunningOnTime();
	} else if (now > ts_simulation) {
		// Not sure how much synchronization overhead is there
		ws->RunningBehind(now - ts_simulation);
	} else {
		ws->RunningOnTime();
	}
}


void WakeupSleepingThreads() {
	{
		lock_guard<mutex> lk(_stop_requested_mutex);
		_stop_requested = true;
	}
	_stop_requested_cv.notify_all();
}


boost::posix_time::ptime SimulationTimeBegin() {
	return _simulation_time_0;
}
boost::posix_time::ptime SimulationTimeEnd() {
	return _simulation_time_3;
}
boost::posix_time::ptime SimulatedTimeBegin() {
	return _simulated_time_0;
}
boost::posix_time::ptime SimulatedTimeEnd() {
	return _simulated_time_3;
}


boost::posix_time::ptime ToSimulatedTime(const boost::posix_time::ptime& simulation_time) {
	boost::posix_time::ptime simulated_time;

	if (_121x_speed_replay) {
		if (simulation_time < _simulation_time_0) {
			THROW("Unexpected");
		} else if (simulation_time < _simulation_time_1) {
			simulated_time = _InterpolateSimulatedTime(_simulated_time_0, _simulated_time_1, _simulation_time_0, _simulation_time_1, simulation_time);
		} else if (simulation_time < _simulation_time_2) {
			simulated_time = _InterpolateSimulatedTime(_simulated_time_1, _simulated_time_2, _simulation_time_1, _simulation_time_2, simulation_time);
		} else if (simulation_time <= _simulation_time_3) {
			simulated_time = _InterpolateSimulatedTime(_simulated_time_2, _simulated_time_3, _simulation_time_2, _simulation_time_3, simulation_time);
		} else {
			// This can happen
			//THROW(boost::format("Unexpected: simulation_3=%s simulation=%s") % Util::ToString(_simulation_time_3) % Util::ToString(_simulation_time));
		}
	} else {
		simulated_time = _InterpolateSimulatedTime(_simulated_time_0, _simulated_time_3, _simulation_time_0, _simulation_time_3, simulation_time);
	}

	return simulated_time;
}


bool StartFromDefined() {
	return _start_from_defined;
}


// Convert to string for saving the ptime conversion computation
const long SimulatedTimeBeginLong() {
	return _simulated_time_begin_long;
}


bool StopAtDefined() {
	return _stop_at_defined;
}


const boost::posix_time::ptime& SimulatedTimeStopAt() {
	return _simulated_time_stop_at;
}

}
