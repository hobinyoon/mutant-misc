rocksdb_dir=$(HOME)/work/mutant/rocksdb

include $(rocksdb_dir)/make_config.mk

ifndef DISABLE_JEMALLOC
	ifdef JEMALLOC
		PLATFORM_CXXFLAGS += "-DROCKSDB_JEMALLOC"
	endif
	EXEC_LDFLAGS := $(JEMALLOC_LIB) $(EXEC_LDFLAGS) -lpthread
	PLATFORM_CXXFLAGS += $(JEMALLOC_INCLUDE)
endif

override CXXFLAGS += -O2 -std=c++11
	
.PHONY: clean librocksdb objs

all: rdb-client

.cpp.o:
	$(CXX) $(CXXFLAGS) $(PLATFORM_CXXFLAGS) -c $< -o $@ -I$(rocksdb_dir)/include

objs = main.o conf.o cons.o util.o

rdb-client: librocksdb $(objs)
	$(CXX) $(CXXFLAGS) -I$(rocksdb_dir)/include \
		$(PLATFORM_LDFLAGS) $(PLATFORM_CXXFLAGS) $(EXEC_LDFLAGS) \
		-Wl,--as-needed -ldl -L$(rocksdb_dir) $(objs) \
		-o$@ \
		-lrocksdb \
		-lboost_filesystem \
		-lboost_program_options \
		-lboost_regex \
		-lboost_system \
		-lboost_timer \
		-lyaml-cpp

clean:
	rm -rf ./rdb-client *.o

librocksdb:
	cd $(rocksdb_dir) && $(MAKE) shared_lib && cd -
