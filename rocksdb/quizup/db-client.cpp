#include <chrono>
#include <boost/regex.hpp>

#include "db-client.h"

#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/slice.h"
#include "rocksdb/table.h"

#include "conf.h"
#include "cons.h"
#include "prog-mon.h"
#include "simtime.h"
#include "util.h"

using namespace rocksdb;
using namespace std;

namespace DbClient {

rocksdb::DB* _db = NULL;
bool _request_db;

void Init() {
	_request_db = Conf::Get("request_db").as<bool>();
	if (! _request_db)
		return;

	if (_db)
		return;

	string db_path = Conf::GetDir("db_path");
	// Create parent directories, in case any of them is missing. DB::Open()
	// creates only the directory requested.
	boost::filesystem::create_directories(db_path);

	Options options;
	// Optimize RocksDB. This is the easiest way to get RocksDB to perform well
	options.IncreaseParallelism();

	// Default memtable memory budget is 512 MB
	options.OptimizeLevelStyleCompaction();

	// If non-zero, we perform bigger reads when doing compaction. If you're
	// running RocksDB on spinning disks, you should set this to at least 2MB.
	// That way RocksDB's compaction is doing sequential instead of random reads.
	//
	// When non-zero, we also force new_table_reader_for_compaction_inputs to
	// true.
	//
	// Default: 0
	options.compaction_readahead_size = 2 * 1024 * 1024;

	// create the DB if it's not already present
	options.create_if_missing = true;

	// 200 GB for each of the db_paths.
	options.db_paths.emplace_back(db_path + "/t0", 200L*1024*1024*1024);
	options.db_paths.emplace_back(Conf::GetStr("slow_dev1_path"), 200L*1024*1024*1024);
	options.db_paths.emplace_back(Conf::GetStr("slow_dev2_path"), 200L*1024*1024*1024);
	options.db_paths.emplace_back(Conf::GetStr("slow_dev3_path"), 200L*1024*1024*1024);

	options.compression = kNoCompression;
	options.compression_per_level.clear();
	for (int i = 0; i < 7; i ++)
		options.compression_per_level.emplace_back(kNoCompression);

	BlockBasedTableOptions bbto;
	bbto.pin_l0_filter_and_index_blocks_in_cache = true;
	bbto.cache_index_and_filter_blocks=true;
	options.table_factory.reset(NewBlockBasedTableFactory(bbto));

	// Mutant options
	options.cache_filter_index_at_all_levels = Conf::Get("cache_filter_index_at_all_levels").as<bool>();
	options.monitor_temp = Conf::Get("monitor_temp").as<bool>();
	options.migrate_sstables = Conf::Get("migrate_sstables").as<bool>();
	options.sst_migration_temperature_threshold = Conf::Get("sst_migration_temperature_threshold").as<double>();
	options.simulation_time_dur_sec = Conf::Get("simulation_time_dur_in_sec").as<double>();
	options.simulated_time_dur_sec  = 1365709.587;

	// Open DB
	Status s = DB::Open(options, db_path, &_db);
	if (! s.ok())
		THROW(boost::format("DB::Open failed: %s") % s.ToString());
}

void Cleanup() {
	if (! _request_db)
		return;

	if (_db) {
		delete _db;
		_db = NULL;
	}
}

void Put(const string& k, const string& v, ProgMon::WorkerStat* ws) {
	auto begin = chrono::high_resolution_clock::now();

	if (_request_db) {
		static const auto wo = WriteOptions();
		Status s = _db->Put(wo, k, v);
		if (! s.ok())
			THROW(boost::format("Put failed: %s") % s.ToString());
	}

	ws->LatencyPut(chrono::duration_cast<chrono::nanoseconds>(chrono::high_resolution_clock::now() - begin).count());
}

void Get(const string& k, string& v, ProgMon::WorkerStat* ws) {
	auto begin = chrono::high_resolution_clock::now();

	if (_request_db) {
		static const auto ro = ReadOptions();
		Status s = _db->Get(ro, k, &v);
		if (s.IsNotFound())
			THROW(boost::format("Key %s not found") % k);
		if (! s.ok())
			THROW(boost::format("Get failed: %s") % s.ToString());
	}

	ws->LatencyGet(chrono::duration_cast<chrono::nanoseconds>(chrono::high_resolution_clock::now() - begin).count());
}

// Atomically apply a set of updates
// Note: might be useful later for record reinsertions
// {
//   WriteBatch batch;
//   batch.Delete("key1");
//   batch.Put("key2", value);
//   s = db->Write(WriteOptions(), &batch);
// }

}
