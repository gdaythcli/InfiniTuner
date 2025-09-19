import configparser
import tempfile
import os
from pydantic import BaseModel
from typing import List

# ===================== Revised BaseModel Definitions =====================

class Version(BaseModel):
    rocksdb_version: str
    options_file_version: str

class DBOptions(BaseModel):
    max_background_flushes: int
    compaction_readahead_size: int
    wal_bytes_per_sync: int
    bytes_per_sync: int
    max_open_files: int
    stats_history_buffer_size: int
    stats_dump_period_sec: int
    stats_persist_period_sec: int
    delete_obsolete_files_period_micros: int
    max_total_wal_size: int
    strict_bytes_per_sync: bool
    delayed_write_rate: int
    avoid_flush_during_shutdown: bool
    writable_file_max_buffer_size: int
    max_subcompactions: int
    max_background_compactions: int
    max_background_jobs: int
    lowest_used_cache_tier: str
    bgerror_resume_retry_interval: int
    max_bgerror_resume_count: int
    best_efforts_recovery: bool
    write_dbid_to_manifest: bool
    avoid_unnecessary_blocking_io: bool
    atomic_flush: bool
    log_readahead_size: int
    dump_malloc_stats: bool
    info_log_level: str
    write_thread_max_yield_usec: int
    max_write_batch_group_size_bytes: int
    wal_compression: str
    write_thread_slow_yield_usec: int
    enable_pipelined_write: bool
    persist_stats_to_disk: bool
    max_manifest_file_size: int
    WAL_size_limit_MB: int
    fail_if_options_file_error: bool
    max_log_file_size: int
    manifest_preallocation_size: int
    listeners: str
    log_file_time_to_roll: int
    allow_data_in_errors: bool
    WAL_ttl_seconds: int
    recycle_log_file_num: int
    file_checksum_gen_factory: str
    keep_log_file_num: int
    db_write_buffer_size: int
    table_cache_numshardbits: int
    use_adaptive_mutex: bool
    allow_ingest_behind: bool
    skip_checking_sst_file_sizes_on_db_open: bool
    random_access_max_buffer_size: int
    access_hint_on_compaction_start: str
    allow_concurrent_memtable_write: bool
    track_and_verify_wals_in_manifest: bool
    skip_stats_update_on_db_open: bool
    compaction_verify_record_count: bool
    paranoid_checks: bool
    max_file_opening_threads: int
    verify_sst_unique_id_in_manifest: bool
    avoid_flush_during_recovery: bool
    flush_verify_memtable_count: bool
    db_host_id: str
    error_if_exists: bool
    wal_recovery_mode: str
    enable_thread_tracking: bool
    is_fd_close_on_exec: bool
    enforce_single_del_contracts: bool
    create_missing_column_families: bool
    create_if_missing: bool
    use_fsync: bool
    wal_filter: str
    allow_2pc: bool
    use_direct_io_for_flush_and_compaction: bool
    manual_wal_flush: bool
    enable_write_thread_adaptive_yield: bool
    use_direct_reads: bool
    allow_mmap_writes: bool
    allow_fallocate: bool
    two_write_queues: bool
    allow_mmap_reads: bool
    unordered_write: bool
    advise_random_on_open: bool

class CFOptions(BaseModel):
    # Original fields
    compaction_style: str
    compaction_filter: str
    num_levels: int
    table_factory: str
    comparator: str
    max_sequential_skip_in_iterations: int
    max_bytes_for_level_base: int
    memtable_prefix_bloom_probes: int
    memtable_prefix_bloom_bits: int
    memtable_prefix_bloom_huge_page_tlb_size: int
    max_successive_merges: int
    arena_block_size: int
    min_write_buffer_number_to_merge: int
    target_file_size_multiplier: int
    source_compaction_factor: int
    max_bytes_for_level_multiplier: float
    max_bytes_for_level_multiplier_additional: List[int]
    compaction_filter_factory: str
    max_write_buffer_number: int
    level0_stop_writes_trigger: int
    compression: str
    level0_file_num_compaction_trigger: int
    purge_redundant_kvs_while_flush: bool
    max_write_buffer_size_to_maintain: int
    memtable_factory: str
    max_grandparent_overlap_factor: int
    expanded_compaction_factor: int
    hard_pending_compaction_bytes_limit: int
    inplace_update_num_locks: int
    level_compaction_dynamic_level_bytes: bool
    level0_slowdown_writes_trigger: int
    filter_deletes: bool
    verify_checksums_in_compaction: bool
    min_partial_merge_operands: int
    paranoid_file_checks: bool
    target_file_size_base: int
    optimize_filters_for_hits: bool
    merge_operator: str
    compression_per_level: List[str]
    compaction_measure_io_stats: bool
    prefix_extractor: str
    bloom_locality: int
    write_buffer_size: int
    disable_auto_compactions: bool
    inplace_update_support: bool

    # Additional fields to cover all keys in the ini file
    memtable_max_range_deletions: int
    block_protection_bytes_per_key: int
    memtable_protection_bytes_per_key: int
    sample_for_compression: int
    blob_file_starting_level: int
    blob_compaction_readahead_size: int
    blob_garbage_collection_force_threshold: float
    enable_blob_garbage_collection: bool
    min_blob_size: int
    last_level_temperature: str
    enable_blob_files: bool
    # target_file_size_base already defined above
    prepopulate_blob_cache: str
    compaction_options_fifo: str
    experimental_mempurge_threshold: float
    bottommost_compression: str
    blob_file_size: int
    memtable_huge_page_size: int
    bottommost_file_compaction_delay: int
    compression_opts: str
    bottommost_compression_opts: str
    blob_garbage_collection_age_cutoff: float
    ttl: int
    soft_pending_compaction_bytes_limit: int
    check_flush_compaction_key_order: bool
    periodic_compaction_seconds: int
    report_bg_io_stats: bool
    compaction_pri: str
    force_consistency_checks: bool
    ignore_max_compaction_bytes_for_input: bool
    default_temperature: str
    level_compaction_dynamic_file_size: bool  # If duplicate, can be removed, but kept here for ini consistency
    memtable_insert_with_hint_prefix_extractor: str
    level_compaction_dynamic_level_bytes: bool  # Same as above, ensure provided in ini
    persist_user_defined_timestamps: bool
    preclude_last_level_data_seconds: int
    preserve_internal_time_seconds: int
    sst_partitioner_factory: str
    max_write_buffer_number_to_maintain: int

class TableOptions(BaseModel):
    num_file_reads_for_auto_readahead: int
    initial_auto_readahead_size: int
    metadata_cache_options: str
    enable_index_compression: bool
    pin_top_level_index_and_filter: bool
    read_amp_bytes_per_bit: int
    verify_compression: bool
    prepopulate_block_cache: str
    format_version: int
    partition_filters: bool
    metadata_block_size: int
    max_auto_readahead_size: int
    index_block_restart_interval: int
    block_size_deviation: int
    block_size: int
    detect_filter_construct_corruption: bool
    no_block_cache: bool
    checksum: str
    filter_policy: str
    data_block_hash_table_util_ratio: float
    block_restart_interval: int
    index_type: str
    pin_l0_filter_and_index_blocks_in_cache: bool
    data_block_index_type: str
    cache_index_and_filter_blocks_with_high_priority: bool
    whole_key_filtering: bool
    index_shortening: str
    cache_index_and_filter_blocks: bool
    block_align: bool
    optimize_filters_for_memory: bool
    flush_block_policy_factory: str

class RocksDBOptions(BaseModel):
    version: Version
    db_options: DBOptions
    cf_options: CFOptions
    table_options: TableOptions

# ===================== Functions to Check Keys in the ini File =====================

# Define mapping between sections and corresponding models (using prefix matching)
SECTION_MODEL_MAP = {
    "Version": Version,
    "DBOptions": DBOptions,
    "CFOptions": CFOptions,
    "TableOptions": TableOptions,
}

def get_model_class(section: str):
    for prefix, model in SECTION_MODEL_MAP.items():
        if section.startswith(prefix):
            return model
    return None

def check_basemodel_keys(ini_file: str):
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case of keys
    config.read(ini_file, encoding="utf-8")

    for section in config.sections():
        model_cls = get_model_class(section)
        if not model_cls:
            print(f"Section [{section}] has no corresponding BaseModel. Skipping check.")
            continue

        model_keys = set(model_cls.__fields__.keys())
        ini_keys = set(config.options(section))
        missing_keys = ini_keys - model_keys

        if missing_keys:
            print(f"The following keys in section [{section}] are missing in the model {model_cls.__name__}:")
            for key in sorted(missing_keys):
                print(f"  - {key}")
        else:
            print(f"All keys in section [{section}] are defined in the model {model_cls.__name__}.")

# ===================== Test Run =====================

# Write ini file content to a temporary file (content sourced from your ini text)
ini_content = """[Version]
rocksdb_version=8.8.1
options_file_version=1.1

[DBOptions]
max_background_flushes=-1
compaction_readahead_size=2097152
wal_bytes_per_sync=0
bytes_per_sync=0
max_open_files=-1
stats_history_buffer_size=1048576
stats_dump_period_sec=600
stats_persist_period_sec=600
delete_obsolete_files_period_micros=21600000000
max_total_wal_size=0
strict_bytes_per_sync=false
delayed_write_rate=8388608
avoid_flush_during_shutdown=false
writable_file_max_buffer_size=1048576
max_subcompactions=1
max_background_compactions=-1
max_background_jobs=2
lowest_used_cache_tier=kNonVolatileBlockTier
bgerror_resume_retry_interval=1000000
max_bgerror_resume_count=2147483647
best_efforts_recovery=false
write_dbid_to_manifest=false
avoid_unnecessary_blocking_io=false
atomic_flush=false
log_readahead_size=0
dump_malloc_stats=true
info_log_level=INFO_LEVEL
write_thread_max_yield_usec=100
max_write_batch_group_size_bytes=1048576
wal_compression=kNoCompression
write_thread_slow_yield_usec=3
enable_pipelined_write=true
persist_stats_to_disk=false
max_manifest_file_size=1073741824
WAL_size_limit_MB=0
fail_if_options_file_error=true
max_log_file_size=0
manifest_preallocation_size=4194304
listeners={ErrorHandlerListener:ErrorHandlerListener}
log_file_time_to_roll=0
allow_data_in_errors=false
WAL_ttl_seconds=0
recycle_log_file_num=0
file_checksum_gen_factory=nullptr
keep_log_file_num=1000
db_write_buffer_size=0
table_cache_numshardbits=4
use_adaptive_mutex=false
allow_ingest_behind=false
skip_checking_sst_file_sizes_on_db_open=false
random_access_max_buffer_size=1048576
access_hint_on_compaction_start=NORMAL
allow_concurrent_memtable_write=true
track_and_verify_wals_in_manifest=false
skip_stats_update_on_db_open=false
compaction_verify_record_count=true
paranoid_checks=true
max_file_opening_threads=16
verify_sst_unique_id_in_manifest=true
avoid_flush_during_recovery=false
flush_verify_memtable_count=true
db_host_id=__hostname__
error_if_exists=false
wal_recovery_mode=kPointInTimeRecovery
enable_thread_tracking=false
is_fd_close_on_exec=true
enforce_single_del_contracts=true
create_missing_column_families=true
create_if_missing=true
use_fsync=false
wal_filter=nullptr
allow_2pc=false
use_direct_io_for_flush_and_compaction=true
manual_wal_flush=false
enable_write_thread_adaptive_yield=true
use_direct_reads=true
allow_mmap_writes=false
allow_fallocate=true
two_write_queues=false
allow_mmap_reads=false
unordered_write=false
advise_random_on_open=true

[CFOptions "default"]
memtable_max_range_deletions=0
block_protection_bytes_per_key=0
memtable_protection_bytes_per_key=0
sample_for_compression=0
blob_file_starting_level=0
blob_compaction_readahead_size=0
blob_garbage_collection_force_threshold=1.000000
enable_blob_garbage_collection=false
min_blob_size=0
last_level_temperature=kUnknown
enable_blob_files=false
target_file_size_base=67108864
max_sequential_skip_in_iterations=8
prepopulate_blob_cache=kDisable
compaction_options_fifo={allow_compaction=true;age_for_warm=0;file_temperature_age_thresholds=;max_table_files_size=0;}
max_bytes_for_level_multiplier=10.000000
max_bytes_for_level_multiplier_additional=1:1:1:1:1:1:1
max_bytes_for_level_base=268435456
experimental_mempurge_threshold=0.000000
write_buffer_size=67108864
bottommost_compression=kDisableCompressionOption
prefix_extractor=nullptr
blob_file_size=268435456
memtable_huge_page_size=0
bottommost_file_compaction_delay=0
max_successive_merges=0
compression_opts={max_dict_buffer_bytes=0;checksum=false;use_zstd_dict_trainer=true;enabled=false;parallel_threads=1;zstd_max_train_bytes=0;strategy=0;max_dict_bytes=0;max_compressed_bytes_per_kb=896;level=32767;window_bits=-14;}
arena_block_size=1048576
memtable_whole_key_filtering=false
target_file_size_multiplier=1
max_write_buffer_number=2
blob_compression_type=kNoCompression
compression=kNoCompression
level0_stop_writes_trigger=36
level0_slowdown_writes_trigger=20
level0_file_num_compaction_trigger=4
ignore_max_compaction_bytes_for_input=true
max_compaction_bytes=1677721600
compaction_options_universal={allow_trivial_move=false;incremental=false;stop_style=kCompactionStopStyleTotalSize;compression_size_percent=-1;max_size_amplification_percent=200;max_merge_width=4294967295;min_merge_width=2;size_ratio=1;}
memtable_prefix_bloom_size_ratio=0.000000
hard_pending_compaction_bytes_limit=137438953472
bottommost_compression_opts={max_dict_buffer_bytes=0;checksum=false;use_zstd_dict_trainer=true;enabled=false;parallel_threads=1;zstd_max_train_bytes=0;strategy=0;max_dict_bytes=0;max_compressed_bytes_per_kb=896;level=32767;window_bits=-14;}
blob_garbage_collection_age_cutoff=0.250000
ttl=2592000
soft_pending_compaction_bytes_limit=68719476736
inplace_update_num_locks=10000
paranoid_file_checks=false
check_flush_compaction_key_order=true
periodic_compaction_seconds=0
disable_auto_compactions=false
report_bg_io_stats=false
compaction_pri=kMinOverlappingRatio
compaction_style=kCompactionStyleLevel
merge_operator=nullptr
table_factory=BlockBasedTable
memtable_factory=SkipListFactory
comparator=leveldb.BytewiseComparator
compaction_filter_factory=nullptr
num_levels=7
min_write_buffer_number_to_merge=1
bloom_locality=0
max_write_buffer_size_to_maintain=0
sst_partitioner_factory=nullptr
preserve_internal_time_seconds=0
preclude_last_level_data_seconds=0
max_write_buffer_number_to_maintain=0
default_temperature=kUnknown
optimize_filters_for_hits=false
level_compaction_dynamic_file_size=true
memtable_insert_with_hint_prefix_extractor=nullptr
level_compaction_dynamic_level_bytes=false
inplace_update_support=false
persist_user_defined_timestamps=true
compaction_filter=nullptr
force_consistency_checks=true

[TableOptions/BlockBasedTable "default"]
num_file_reads_for_auto_readahead=2
initial_auto_readahead_size=8192
metadata_cache_options={unpartitioned_pinning=kFallback;partition_pinning=kFallback;top_level_index_pinning=kFallback;}
enable_index_compression=true
pin_top_level_index_and_filter=false
read_amp_bytes_per_bit=0
verify_compression=false
prepopulate_block_cache=kDisable
format_version=5
partition_filters=false
metadata_block_size=4096
max_auto_readahead_size=262144
index_block_restart_interval=1
block_size_deviation=10
block_size=4096
detect_filter_construct_corruption=false
no_block_cache=false
checksum=kXXH3
filter_policy=nullptr
data_block_hash_table_util_ratio=0.750000
block_restart_interval=16
index_type=kBinarySearch
pin_l0_filter_and_index_blocks_in_cache=false
data_block_index_type=kDataBlockBinarySearch
cache_index_and_filter_blocks_with_high_priority=true
whole_key_filtering=true
index_shortening=kShortenSeparatorsAndSuccessor
cache_index_and_filter_blocks=false
block_align=false
optimize_filters_for_memory=false
flush_block_policy_factory=FlushBlockBySizePolicyFactory
"""

# Write ini file content to a temporary file (content sourced from your ini text)
with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ini", encoding="utf-8") as tmp:
    tmp.write(ini_content)
    tmp_filename = tmp.name

print("Using temporary ini file:", tmp_filename)
print("=" * 60)
# Run the check function
check_basemodel_keys(tmp_filename)
# Delete the temporary file
os.remove(tmp_filename)
