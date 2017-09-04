#include <csignal>
#include <cstdio>
#include <string>

#include <boost/format.hpp>

#include "conf.h"
#include "cons.h"
#include "db-client.h"
#include "simtime.h"
#include "util.h"
#include "workload-player.h"

using namespace std;


void on_signal(int sig) {
  if (sig == SIGINT) {
    cout << "Interrupted. Stopping workers ...\n";
    WorkloadPlayer::Stop();
    return;
  }

  cout << boost::format("\nGot a signal: %d\n%s\n") % sig % Util::Indent(Util::StackTrace(1), 2);
  exit(1);
}


// Copy the DB LOG file and client log file to log archive directory, and zip them.
// Archiving logs here is easier so that we don't have to pass the simulation_time_begin to the calling script.
void ArchiveLogs() {
  Cons::MT _("Archiving logs ...");

  string sbt = Util::ToString(SimTime::SimulationTime0());

  // DB LOG
  string fn_db0 = str(boost::format("%s/LOG") % Conf::GetDir("db_path"));
  string dn1 = str(boost::format("%s/rocksdb") % Conf::GetDir("log_archive_dn"));
  string fn_db1 = str(boost::format("%s/%s") % dn1 % sbt);
  boost::filesystem::create_directories(dn1);
  boost::filesystem::copy_file(fn_db0, fn_db1);

  // QuizUp client log
  const string& fn_c0 = ProgMon::FnClientLog();
  dn1 = str(boost::format("%s/quizup") % Conf::GetDir("log_archive_dn"));
  string fn_c1 = str(boost::format("%s/%s") % dn1 % sbt);
  boost::filesystem::create_directories(dn1);
  boost::filesystem::copy_file(fn_c0, fn_c1);

  // Zip them
  Util::RunSubprocess(str(boost::format("7z a -mx %s.7z %s >/dev/null 2>&1") % fn_db1 % fn_db1));
  // Quizup client log will be zipped by the calling script after the configuration parameters added.
  //Util::RunSubprocess(str(boost::format("7z a -mx %s.7z %s >/dev/null 2>&1") % fn_c1 % fn_c1));
}


int main(int argc, char* argv[]) {
  try {
    signal(SIGSEGV, on_signal);
    signal(SIGINT, on_signal);

    Conf::Init(argc, argv);
    DbClient::Init();

    WorkloadPlayer::Run();
    DbClient::Cleanup();
    ArchiveLogs();
  } catch (const exception& e) {
    cerr << "Got an exception: " << e.what() << "\n";
    return 1;
  }
  return 0;
}
