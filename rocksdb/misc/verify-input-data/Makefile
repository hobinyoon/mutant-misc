#override CXXFLAGS += -g -O2 -std=c++11
override CXXFLAGS += -O2 -std=c++11
	
.PHONY: clean objs

all: verify

.cpp.o:
	$(CXX) $(CXXFLAGS) $(PLATFORM_CXXFLAGS) -c $< -o $@

objs = main.o conf.o cons.o prog-mon.o simtime.o util.o verify.o

verify: $(objs)
	$(CXX) $(CXXFLAGS) \
		$(objs) \
		-o$@ \
		-lpthread \
		-lboost_filesystem \
		-lboost_program_options \
		-lboost_regex \
		-lboost_system \
		-lboost_thread \
		-lboost_timer \
		-lyaml-cpp

clean:
	rm -rf ./verify *.o
