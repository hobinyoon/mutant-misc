#pragma once

#include <boost/date_time/posix_time/posix_time.hpp>

#include "prog-mon.h"

namespace SimTime {
	void Init1();
	void Init2();
	void Cleanup();

	void MaySleepUntilSimulatedTime(const boost::posix_time::ptime& ts_simulated
			, ProgMon::WorkerStat* ws);
	void WakeupSleepingThreads();

	boost::posix_time::ptime SimulationTimeBegin();
	boost::posix_time::ptime SimulationTimeEnd();
	boost::posix_time::ptime SimulatedTimeBegin();
	boost::posix_time::ptime SimulatedTimeEnd();

	boost::posix_time::ptime ToSimulatedTime(const boost::posix_time::ptime& simulation_time0);
	std::string ToSimulatedTimeStr(const boost::posix_time::ptime& simulation_time0);

	bool StartFromDefined();
	const long SimulatedTimeBeginLong();
	bool StopAtDefined();
	const boost::posix_time::ptime& SimulatedTimeStopAt();
}
