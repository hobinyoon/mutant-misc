#pragma once

#include <boost/date_time/posix_time/posix_time.hpp>

#include "prog-mon.h"

namespace SimTime {
	void Init1();
	void Init2();
	void Cleanup();

	int MaySleepUntilSimulatedTime(const boost::posix_time::ptime& ts_simulated
			, ProgMon::WorkerStat* ws);
	void WakeupSleepingThreads();

	boost::posix_time::ptime SimulationTime0();
	boost::posix_time::ptime SimulationTime1();
	boost::posix_time::ptime SimulationTime2();
	boost::posix_time::ptime SimulationTime3();
	boost::posix_time::ptime SimulationTime4();
	boost::posix_time::ptime SimulatedTime0();
	boost::posix_time::ptime SimulatedTime1();
	boost::posix_time::ptime SimulatedTime2();
	boost::posix_time::ptime SimulatedTime3();
	boost::posix_time::ptime SimulatedTime4();

	boost::posix_time::ptime ToSimulatedTime(const boost::posix_time::ptime& simulation_time0);
	std::string ToSimulatedTimeStr(const boost::posix_time::ptime& simulation_time0);

	bool StartFromDefined();
	const long SimulatedTimeBeginLong();
	bool StopAtDefined();
	const boost::posix_time::ptime& SimulatedTimeStopAt();
}
