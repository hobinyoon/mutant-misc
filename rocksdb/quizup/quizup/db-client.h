#pragma once

#include <string>

#include "prog-mon.h"

namespace DbClient {
  void Init();
  void Cleanup();

  void Put(const std::string& k, const std::string& v, ProgMon::WorkerStat* ws);
  void Get(const std::string& k, std::string& v, ProgMon::WorkerStat* ws);

  void SetSstOtt(double sst_ott);
}
