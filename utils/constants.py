import os
from dotenv import load_dotenv
import argparse
from datetime import datetime

load_dotenv()

def path_of_output_folder():
    '''
    Set the output folder directory

    Parameters:
    - None

    Returns:
    - output_folder_dir (str): The output folder directory
    '''
    current_datetime = datetime.now()
    date_time_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    output_folder_dir = f"output/output_{DEVICE}/output_{date_time_string}"

    os.makedirs(output_folder_dir, exist_ok=True)
    print(f"[UTL] Using output folder: {output_folder_dir}")

    return output_folder_dir

def path_of_records_folder():
    '''
    Set the records folder directory

    Parameters:
    - None

    Returns:
    - records_folder_dir (str): The records folder directory
    '''
    current_datetime = datetime.now()
    date_time_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    records_folder_dir = f"records/records_{date_time_string}"

    os.makedirs(records_folder_dir, exist_ok=True)
    print(f"[UTL] Using records folder: {records_folder_dir}")

    return records_folder_dir

def path_of_examples_folder():
    '''
    Set the examples folder directory

    Parameters:
    - None

    Returns:
    - examples_folder_dir (str): The examples folder directory
    '''
    current_datetime = datetime.now()
    date_time_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    examples_folder_dir = f"examples/examples_{date_time_string}"

    os.makedirs(examples_folder_dir, exist_ok=True)
    print(f"[UTL] Using examples folder: {examples_folder_dir}")

    return examples_folder_dir

def path_of_insights_folder():
    '''
    Set the insights folder directory

    Parameters:
    - None

    Returns:
    - insights_folder_dir (str): The insights folder directory
    '''
    # current_datetime = datetime.now()
    # date_time_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    insights_folder_dir = "insights"
    os.makedirs(insights_folder_dir, exist_ok=True)
    print(f"[UTL] Using insights folder: {insights_folder_dir}")
    return insights_folder_dir

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected!')


# Workload, Device, and LSM-KVS Version Constants
env_DEVICE = os.getenv("DEVICE", "data")
env_ITERATION_COUNT = os.getenv("ITERATION_COUNT", 3)
env_TEST_NAME = os.getenv("TEST_NAME", "fillrandom")
env_CASE_NUMBER = os.getenv("CASE_NUMBER", 3)
env_VERSION = os.getenv("VERSION", "8.8.1")
env_OUTPUT_PATH = os.getenv("OUTPUT_PATH", None)
env_RECORDS_PATH = os.getenv("RECORDS_PATH", None)
env_EXAMPLES_PATH = os.getenv("EXAMPLES_PATH", None)
env_INSIGHTS_PATH = os.getenv("INSIGHTS_PATH", None)
env_NUM_ENTRIES = os.getenv("NUM_ENTRIES", 25000000)
env_NUM_THREADS = os.getenv("NUM_THREADS", 1)
env_DURATION = os.getenv("DURATION", 60)
env_SINE_WRITE_RATE_INTERVAL_MILLISECONDS = os.getenv("SINE_WRITE_RATE_INTERVAL_MILLISECONDS", 1000)
env_SINE_A = os.getenv("SINE_A", 2000000) # 2M/80 for ~ 25k ops/sec
env_SINE_B = os.getenv("SINE_B", 2.3873241464) # 15/(2*pi) for a 30 second period
env_SINE_C = os.getenv("SINE_C", 0)
env_SINE_D = os.getenv("SINE_D", 10000000) # 10M/80 for ~ 125k ops/sec

# Sesame Controller Constants
env_SIDE_CHECKER = str2bool(os.getenv("SIDE_CHECKER", True))
env_ERROR_CORRECTION_COUNT = os.getenv("ERROR_CORRECTION_COUNT", 2)
env_FINETUNE_ITERATION = os.getenv("FINETUNE_ITERATION", 2)
env_DYNAMIC_OPTION_TUNING = os.getenv("DYNAMIC_OPTION_TUNING", False)
env_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
env_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
env_RAG = str2bool(os.getenv("RAG", False))
env_ABSTRACTION = str2bool(os.getenv("ABSTRACTION", False))
env_TRACEFILE_PATH = os.getenv("TRACEFILE_PATH", None)
env_PRE_LOAD_CMD = os.getenv("PRE_LOAD_CMD", None)
# If the pre-load db path is set, Sesame will simply copy the db to the db path
# If the pre-load db path is not set, Sesame will run the pre-load command
env_PRE_LOAD_DB_PATH = os.getenv("PRE_LOAD_DB_PATH", "")
env_ENABLE_MCTS = str2bool(os.getenv("ENABLE_MCTS", True))
env_ENABLE_ONE_SHOT = str2bool(os.getenv("ENABLE_ONE_SHOT", True))
env_ENABLE_UNKNOWN = str2bool(os.getenv("ENABLE_UNKNOWN", False))
env_LOAD_RECORDS = str2bool(os.getenv("LOAD_RECORDS", False))


# Parse the arguments. They replace the environment variables if they are set
parser = argparse.ArgumentParser(description='Description of your script')
parser.add_argument('-i', '--iteration_count', type=int, default=env_ITERATION_COUNT, help='Specify the number of iterations')
parser.add_argument('-c', '--case', type=int, default=env_CASE_NUMBER, help='Specify the case number')
parser.add_argument('-d', '--device', type=str, default=env_DEVICE, help='Specify the device')
parser.add_argument('-t', '--workload', type=str, default=env_TEST_NAME, help='Specify the test name')
parser.add_argument('-v', '--version', type=str, default=env_VERSION, help='Specify the version of RocksDB')
parser.add_argument('-o', '--output', type=str, default=env_OUTPUT_PATH, help='Specify the output path')
parser.add_argument('-n', '--num_entries', type=int, default=env_NUM_ENTRIES, help='Specify the number of entries')
parser.add_argument('-th', '--num_threads', type=int, default=env_NUM_THREADS, help='Specify the number of threads')
parser.add_argument('-u', '--duration', type=int, default=env_DURATION, help='Specify the duration')
parser.add_argument('-s', '--side_checker', type=str2bool, default=env_SIDE_CHECKER, help='Specify if side checker is enabled')
parser.add_argument('-ec', '--error_correction_count', type=int, default=env_ERROR_CORRECTION_COUNT, help='Specify the error correction count')
parser.add_argument('-f', '--finetune_iteration', type=int, default=env_FINETUNE_ITERATION, help='Specify the Number of Fine-Tuning Iterations')
parser.add_argument('-dt', '--dynamic_option_tuning', type=str2bool, default=env_DYNAMIC_OPTION_TUNING, help='Specify if dynamic option tuning is enabled')
parser.add_argument('-m', '--llm_model', type=str, default=env_LLM_MODEL, help='Specify the LLM model to use')
parser.add_argument('-e', '--embedding_model', type=str, default=env_EMBEDDING_MODEL, help='Specify the embedding model to use')
parser.add_argument('-r', '--rag', type=str2bool, default=env_RAG, help='Specify if RAG is enabled')
parser.add_argument('-a', '--abstraction', type=str2bool, default=env_ABSTRACTION, help='Specify if using Abstraction or not')
parser.add_argument('--tracefile_path', type=str, default=env_TRACEFILE_PATH, help='Specify the path of the tracefile')
parser.add_argument('--pre_load_cmd', type=str, default=env_PRE_LOAD_CMD, help='Specify the pre-load command')
parser.add_argument('--pre_load_db_path', type=str, default=env_PRE_LOAD_DB_PATH, help='Specify the pre-load db path')
parser.add_argument('--enable_mcts', type=str2bool, default=env_ENABLE_MCTS, help='Specify if MCTS is enabled')
parser.add_argument('--enable_one_shot', type=str2bool, default=env_ENABLE_ONE_SHOT, help='Specify if one shot is enabled')
parser.add_argument('-rd', '--records', type=str, default=env_RECORDS_PATH, help='Specify the records path')
parser.add_argument('-exp', '--examples', type=str, default=env_EXAMPLES_PATH, help='Specify the examples path')
parser.add_argument('-ins', '--insights', type=str, default=env_INSIGHTS_PATH, help='Specify the insights path')
parser.add_argument('--enable_unknown', type=str2bool, default=env_ENABLE_UNKNOWN, help='Specify if unknown is enabled')
parser.add_argument('--load_records', type=str2bool, default=env_LOAD_RECORDS, help='Specify if load records is enabled')
parser.add_argument('--sine_write_rate_interval_milliseconds', type=int, default=env_SINE_WRITE_RATE_INTERVAL_MILLISECONDS, help='Specify the sine write rate interval in milliseconds')
parser.add_argument('--sine_a', type=float, default=env_SINE_A, help='Specify the sine parameter a')
parser.add_argument('--sine_b', type=float, default=env_SINE_B, help='Specify the sine parameter b')
parser.add_argument('--sine_c', type=float, default=env_SINE_C, help='Specify the sine parameter c')
parser.add_argument('--sine_d', type=float, default=env_SINE_D, help='Specify the sine parameter d')

args = parser.parse_args()
ITERATION_COUNT = args.iteration_count
CASE_NUMBER = args.case
DEVICE = args.device
TEST_NAME = args.workload
VERSION = args.version
OUTPUT_PATH = args.output if args.output else path_of_output_folder()
RECORDS_PATH = args.records if args.records else path_of_records_folder()
EXAMPLES_PATH = args.examples if args.examples else path_of_examples_folder()
INSIGHTS_PATH = args.insights if args.insights else path_of_insights_folder()
NUM_ENTRIES = args.num_entries
NUM_THREADS = args.num_threads
DURATION = args.duration
SIDE_CHECKER = args.side_checker
ERROR_CORRECTION_COUNT = args.error_correction_count
FINETUNE_ITERATION = args.finetune_iteration
DYNAMIC_OPTION_TUNING = args.dynamic_option_tuning
LLM_MODEL = args.llm_model
EMBEDDING_MODEL = args.embedding_model
RAG = args.rag
ABSTRACTION = args.abstraction
TRACEFILE_PATH = args.tracefile_path
PRE_LOAD_CMD = args.pre_load_cmd
PRE_LOAD_DB_PATH = args.pre_load_db_path
ENABLE_MCTS = args.enable_mcts
ENABLE_ONE_SHOT = args.enable_one_shot
ENABLE_UNKNOWN = args.enable_unknown
LOAD_RECORDS = args.load_records
SINE_WRITE_RATE_INTERVAL_MILLISECONDS = args.sine_write_rate_interval_milliseconds
SINE_A = args.sine_a
SINE_B = args.sine_b
SINE_C = args.sine_c
SINE_D = args.sine_d

# Path Constants locally

# HOME_PATH = f"/home/bob"
# DB_BENCH_PATH = os.path.join(HOME_PATH, f"rocksdb-8.8.1/db_bench")
# TRACE_ANALYZER_PATH = os.path.join(HOME_PATH, f"rocksdb-8.8.1/trace_analyzer")
# DB_PATH = os.path.join(HOME_PATH, f"gpt_project/db")
# FIO_RESULT_PATH = os.path.join(HOME_PATH, f"fio/fio_output_{DEVICE}.txt")

DB_BENCH_PATH = f"/home/alice/rocksdb-8.8.1/db_bench"
TRACE_ANALYZER_PATH = f"/home/alice/rocksdb-8.8.1/trace_analyzer"
DB_PATH = f"/home/alice/gpt_project/db"
FIO_RESULT_PATH = f"/home/alice/fio/fio_output_{DEVICE}.txt"

DEFAULT_OPTION_FILE_DIR = "options_files/default_options_files"
INITIAL_OPTIONS_FILE_NAME = f"dbbench_default_options-{VERSION}.ini"
OPTIONS_FILE_DIR = f"{OUTPUT_PATH}/options_file.ini"
RECORDS_FILE_DIR = f"{RECORDS_PATH}/records.txt"
EXAMPLES_FILE_DIR = f"{EXAMPLES_PATH}/examples.txt"
POSITIVE_INSIGHTS_FILE_DIR = f"{INSIGHTS_PATH}/positive_insights.txt"
NEGATIVE_INSIGHTS_FILE_DIR = f"{INSIGHTS_PATH}/negative_insights.txt"

# Path Constants docker
# DB_BENCH_PATH = f"/rocksdb-{VERSION}/db_bench"
# TRACE_ANALYZER_PATH = f"/rocksdb-{VERSION}/trace_analyzer"
# DB_PATH = f"/{DEVICE}/gpt_project/db"
# FIO_RESULT_PATH = f"data/fio/fio_output_{DEVICE}.txt"
# DEFAULT_OPTION_FILE_DIR = "options_files/default_options_files"
# INITIAL_OPTIONS_FILE_NAME = f"dbbench_default_options-{VERSION}.ini"
# OPTIONS_FILE_DIR = f"{OUTPUT_PATH}/options_file.ini"
