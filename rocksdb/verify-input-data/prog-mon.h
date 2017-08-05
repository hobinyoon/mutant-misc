#pragma once

#include <boost/date_time/posix_time/posix_time.hpp>

namespace ProgMon {

void IncTotalNumOps(size_t s);

void ReporterStart();
void ReporterStop();

void RunningOnTime();
void RunningBehind(const boost::posix_time::time_duration& td);

void LatencyPut(const long d);
void LatencyGet(const long d);

}
