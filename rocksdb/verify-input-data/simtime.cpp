#include <condition_variable>
#include <mutex>
#include <thread>
#include <boost/thread/thread.hpp>

#include "conf.h"
#include "cons.h"
#include "prog-mon.h"
#include "simtime.h"
#include "util.h"

using namespace std;

namespace SimTime {

boost::posix_time::ptime simulation_time_begin;
boost::posix_time::ptime simulation_time_end;
boost::posix_time::ptime simulated_time_begin;
boost::posix_time::ptime simulated_time_end;

mutex _stop_requested_mutex;
bool _stop_requested = false;
condition_variable _stop_requested_cv;

// Calculate simulation / simulated time.  Set the simulation_time_begin 0.01
// sec after now.
//
// Not sure how to construct a std::chrono::time_point from a string with
// microsecond resolution. Go with boost::ptime. Hope it's not too slow.
void Init() {
	Cons::MT _("Init SimTime ...", false);

	boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
	simulation_time_begin = now + boost::posix_time::milliseconds(10);
	simulation_time_end = simulation_time_begin + boost::posix_time::seconds(Conf::Get("simulation_time_dur_in_sec").as<int>());
	simulated_time_begin = Util::ToPtime(Conf::GetStr("simulated_time_begin"));
	simulated_time_end   = Util::ToPtime(Conf::GetStr("simulated_time_end"));

	Cons::P(boost::format("simulation_time_begin: %s") % Util::ToString(simulation_time_begin));
	Cons::P(boost::format("simulation_time_end  : %s") % Util::ToString(simulation_time_end));
	Cons::P(boost::format("simulated_time_begin : %s") % Util::ToString(simulated_time_begin));
	Cons::P(boost::format("simulated_time_end   : %s") % Util::ToString(simulated_time_end));
}


// simulation_time_begin : a (ts_simulation) : simulation_time_end
// simulated_time_begin  : b (ts_simulated)  : simulated_time_end
//
// a - simulation_time_begin : b - simulated_time_begin = simulation_time_end - simulation_time_begin : simulated_time_end - simulated_time_begin
// a - simulation_time_begin = (b - simulated_time_begin) * (simulation_time_end - simulation_time_begin) / (simulated_time_end - simulated_time_begin)
// a = (b - simulated_time_begin) * (simulation_time_end - simulation_time_begin) / (simulated_time_end - simulated_time_begin) + simulation_time_begin
//
// Note: Pre-calculate the constants if needed
void MaySleepUntilSimulatedTime(const boost::posix_time::ptime& ts_simulated) {
	// With a ns resolution, long can contain up to 292 years. Good enough.
	//   calc "(2^63 - 1) / (10^9) / 3600 / 24 / 365.25"
	//   = 292 years

	auto td = boost::posix_time::time_duration(0, 0, 0,
			double((ts_simulated - simulated_time_begin).total_nanoseconds())
			* double((simulation_time_end - simulation_time_begin).total_nanoseconds())
			/ double((simulated_time_end - simulated_time_begin).total_nanoseconds())
			/ 1000.0
			);
	auto ts_simulation = simulation_time_begin + td;

	boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
	if (now < ts_simulation) {
		auto sleep_dur = (ts_simulation - now).total_nanoseconds();
		{
			// I'm hoping this is reentrant by multiple worker threads. Looks like
			// because wait_for() unlocks the mutex.
			unique_lock<mutex> lk(_stop_requested_mutex);
			_stop_requested_cv.wait_for(lk, chrono::nanoseconds(sleep_dur), [](){return _stop_requested;});
		}

		ProgMon::RunningOnTime();
	} else if (now > ts_simulation) {
		// Not sure how much synchronization overhead is there
		ProgMon::RunningBehind(now - ts_simulation);
	} else {
		ProgMon::RunningOnTime();
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
	return simulation_time_begin;
}


// simulation_time_begin : a (ts_simulation) : simulation_time_end
// simulated_time_begin  : b (ts_simulated)  : simulated_time_end
//
// b - simulated_time_begin = (a - simulation_time_begin) * (simulated_time_end - simulated_time_begin) / (simulation_time_end - simulation_time_begin)
// b = (a - simulation_time_begin) * (simulated_time_end - simulated_time_begin) / (simulation_time_end - simulation_time_begin) + simulated_time_begin
//
// Note: Pre-calculate the constants if needed
boost::posix_time::ptime ToSimulatedTime(const boost::posix_time::ptime& simulation_time0) {
	// The default time_duration precision seems to be microsecond from an
	// experiment. Not sure how to change it. Might be a system-wide
	// configuration.
	//   boost::posix_time::time_duration td(0, 0, 0, 1);
	//   cout << td << "\n";
	auto td = boost::posix_time::time_duration(0, 0, 0,
				double((simulation_time0 - simulation_time_begin).total_nanoseconds())
				* double((simulated_time_end - simulated_time_begin).total_nanoseconds())
				/ double((simulation_time_end - simulation_time_begin).total_nanoseconds())
				/ 1000.0
				);
	auto t = simulated_time_begin + td;
	return t;
}

}
