#include <csignal>
#include <cstdio>
#include <string>

#include <boost/format.hpp>

#include "conf.h"
#include "cons.h"
#include "verify.h"
#include "util.h"

using namespace std;


void on_signal(int sig) {
	cout << boost::format("\nGot a signal: %d\n%s\n") % sig % Util::Indent(Util::StackTrace(1), 2);
  exit(1);
}


int main(int argc, char* argv[]) {
	try {
		signal(SIGSEGV, on_signal);
		signal(SIGINT, on_signal);

		Conf::Init(argc, argv);

		Verify::Run();
	} catch (const exception& e) {
		cerr << "Got an exception: " << e.what() << "\n";
		return 1;
	}
	return 0;
}
