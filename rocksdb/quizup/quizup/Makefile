rocksdb_dir=$(HOME)/work/mutant/rocksdb

include $(rocksdb_dir)/make_config.mk

ifndef DISABLE_JEMALLOC
	ifdef JEMALLOC
		PLATFORM_CXXFLAGS += "-DROCKSDB_JEMALLOC"
	endif
	EXEC_LDFLAGS := $(JEMALLOC_LIB) $(EXEC_LDFLAGS) -lpthread
	PLATFORM_CXXFLAGS += $(JEMALLOC_INCLUDE)
endif

#override CXXFLAGS += -g
# http://stackoverflow.com/questions/35007134/c-boost-undefined-reference-to-boostfilesystemdetailcopy-file
override CXXFLAGS += -O2 -std=c++11 -DBOOST_NO_CXX11_SCOPED_ENUMS


.PHONY: clean librocksdb objs

all: quizup

.cpp.o:
	$(CXX) $(CXXFLAGS) $(PLATFORM_CXXFLAGS) -c $< -o $@ -I$(rocksdb_dir)/include -I$(rocksdb_dir)/mutant

objs = main.o conf.o cons.o db-client.o prog-mon.o simtime.o util.o workload-player.o

quizup: librocksdb $(objs)
	$(CXX) $(CXXFLAGS) -I$(rocksdb_dir)/include \
		$(PLATFORM_LDFLAGS) $(PLATFORM_CXXFLAGS) $(EXEC_LDFLAGS) \
		-Wl,--as-needed -ldl -L$(rocksdb_dir) $(objs) \
		-o$@ \
		-lpthread \
		-lrocksdb \
		-lboost_filesystem \
		-lboost_iostreams \
		-lboost_program_options \
		-lboost_regex \
		-lboost_system \
		-lboost_thread \
		-lboost_timer \
		-ljsoncpp \
		-lyaml-cpp

clean:
	rm -rf ./quizup *.o

librocksdb:
	cd $(rocksdb_dir) && $(MAKE) shared_lib && cd -
