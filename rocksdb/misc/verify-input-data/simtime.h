#pragma once

#include <boost/date_time/posix_time/posix_time.hpp>

namespace SimTime {
	void Init();
	void Cleanup();

	void MaySleepUntilSimulatedTime(const boost::posix_time::ptime& ts_simulated);
	void WakeupSleepingThreads();

	boost::posix_time::ptime SimulationTimeBegin();

	boost::posix_time::ptime ToSimulatedTime(const boost::posix_time::ptime& simulation_time0);
	std::string ToSimulatedTimeStr(const boost::posix_time::ptime& simulation_time0);
}
