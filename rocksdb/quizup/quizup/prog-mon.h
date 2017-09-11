#pragma once

#include <mutex>
#include <vector>
#include <boost/date_time/posix_time/posix_time.hpp>

namespace ProgMon {

// Per worker thread counters to avoid a lock bottleneck
class WorkerStat {
  std::mutex _mutex_running_on_time;
  long _running_on_time_cnt = 0;

  std::mutex _mutex_running_behind;
  long _running_behind_cnt = 0;
  long _running_behind_dur = 0;

  std::mutex _mutex_latency_put;
  std::vector<long> _latency_put;

  std::mutex _mutex_latency_get;
  std::vector<long> _latency_get;

public:
  void RunningOnTime();
  void RunningBehind(const boost::posix_time::time_duration& td);
  void LatencyPut(const long d);
  void LatencyGet(const long d);
  void GetAndReset(
      long& running_on_time_cnt,
      long& running_behind_cnt,
      long& running_behind_dur,
      std::vector<long>& latency_put,
      std::vector<long>& latency_get);
};

void IncTotalNumOps(size_t s);

WorkerStat* GetWorkerStat();

void ReporterStart();
void ReporterStop();

const std::string& FnClientLog();

void StartReportingToSlaAdmin();

void UpdateXrQLen(size_t s);

}
