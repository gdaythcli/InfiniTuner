from search.search_utils import Node, get_node_by_id, bfs_collect_digests
from utils.utils import path_of_db, log_update
import utils.constants as constants
import os
import subprocess
import time

from utils.constants import *
from utils.cgroup_manager import CGroupManager
from utils.cgroup_monitor import CGroupMonitor
import re
from gpt.content_generator import error_correction_options_file_generation
from search.summary_agent import summary_benchmark
import json


def pre_tasks(database_path, run_count):
    """

    Function to perform the pre-tasks before running the db_bench
    Parameters:
    - database_path (str): The path to the database
    - run_count (str): The current iteration of the benchmark

    Returns:
    - None
    """

    # Try to delete the database if path exists
    proc = subprocess.run(
        f"rm -rf {database_path}",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        check=False,

    )

    log_update("[SPM] Flushing the cache")
    print("[SPM] Flushing the cache")
    # Delay for all the current memory to be freed
    proc = subprocess.run(
        f"sync; echo 3 > /proc/sys/vm/drop_caches",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        check=False,

    )

    # update_log_file("[SPM] Waiting for 90 seconds to free up memory, IO and other resources")
    print("[SPM] Waiting for 10 seconds to free up memory, IO and other resources")
    # Give a 1.5 min delay for all the current memory/IO/etc to be freed
    time.sleep(10)



def parse_db_bench_output(output):
    err_check = re.search("Unable to load options file", output) or re.search(
        "open error", output
    )
    if err_check is not None:
        error = output[err_check.span()[0] :]

        return {
            "error": error,
            "ops_per_sec": None,
        }

    # Regular expression to find and extract the number of Entries
    # Searches for the pattern "Entries:" followed by one or more digits
    entries_match = re.search(r"Entries:\s+(\d+)", output)
    # If a match is found, convert the captured digits to an integer
    entries = int(entries_match.group(1)) if entries_match else None

    # Regular expression to parse the output line
    # Captures various performance metrics and their units
    test_name = None

    if "readrandomwriterandom" in output:
        op_line = output.split("readrandomwriterandom")[1].split("\n")[0]
        test_name = "readrandomwriterandom"
        test_pattern = r"readrandomwriterandom\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;"
    elif "jsonconfigured" in output:
        op_line = output.split("jsonconfigured")[1].split("\n")[0]
        test_name = "jsonconfigured"
        test_pattern = r"jsonconfigured\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;"
    elif "fillrandom" in output:
        op_line = output.split("fillrandom")[1].split("\n")[0]
        test_name = "fillrandom"
        test_pattern = r"fillrandom\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;\s+(\d+\.\d+)\s+(\w+/s)\nMicroseconds per write:\nCount:\s+(\d+)\s+Average:\s+(\d+\.\d+)\s+StdDev:\s+(\d+\.\d+)\nMin:\s+(\d+)\s+Median:\s+(\d+\.\d+)\s+Max:\s+(\d+)\nPercentiles:\s+P50:\s+(\d+\.\d+)\s+P75:\s+(\d+\.\d+)\s+P99:\s+(\d+\.\d+)\s+P99\.9:\s+(\d+\.\d+)\s+P99\.99:\s+(\d+\.\d+)\n-{50}"
    elif "readrandom" in output:
        op_line = output.split("readrandom")[1].split("\n")[0]
        test_name = "readrandom"
        test_pattern = r"readrandom\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;\s+(\d+\.\d+)\s+(\w+/s)\s+\((\d+)\s+of\s+(\d+)\s+found\)\n\nMicroseconds per read:\nCount:\s+(\d+)\s+Average:\s+(\d+\.\d+)\s+StdDev:\s+(\d+\.\d+)\nMin:\s+(\d+)\s+Median:\s+(\d+\.\d+)\s+Max:\s+(\d+)\nPercentiles:\s+P50:\s+(\d+\.\d+)\s+P75:\s+(\d+\.\d+)\s+P99:\s+(\d+\.\d+)\s+P99\.9:\s+(\d+\.\d+)\s+P99\.99:\s+(\d+\.\d+)\n-{50}"
    elif "mixgraph" in output:
        op_line = output.split("mixgraph     :")[1].split("\n")[0]
        test_name = "mixgraph"
        test_pattern = r"mixgraph\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;"
        # test_pattern = r"mixgraph\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;\s+\(\s+Gets:+(\d+)\s+Puts:+(\d+)\s+Seek:(\d+),\s+reads\s+(\d+)\s+in\s+(\d+)\s+found,\s+avg\s+size:\s+\d+\s+value,\s+-nan\s+scan\)\n\nMicroseconds per read:\nCount:\s+(\d+)\s+Average:\s+(\d+\.\d+)\s+StdDev:\s+(\d+\.\d+)\nMin:\s+(\d+)\s+Median:\s+(\d+\.\d+)\s+Max:\s+(\d+)\nPercentiles:\s+P50:\s+(\d+\.\d+)\s+P75:\s+(\d+\.\d+)\s+P99:\s+(\d+\.\d+)\s+P99\.9:\s+(\d+\.\d+)\s+P99\.99:\s+(\d+\.\d+)\n-{50}"
    elif "readwhilewriting" in output:
        op_line = output.split("readwhilewriting")[1].split("\n")[0]
        test_name = "readwhilewriting"
        test_pattern = r"readwhilewriting\s+:\s+(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;"
    else:
        log_update(f"[PDB] Test name not found in output: {output}")
        op_line = "unknown test"
        test_name = "unknown"
        test_pattern = r"(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;(\s+\(.*found:\d+\))?\nMicroseconds per (read|write):\nCount: (\d+) Average: (\d+\.\d+)  StdDev: (\d+\.\d+)\nMin: (\d+)  Median: (\d+\.\d+)  Max: (\d+)\nPercentiles: P50: (\d+\.\d+) P75: (\d+\.\d+) P99: (\d+\.\d+) P99.9: (\d+\.\d+) P99.99: (\d+\.\d+)"

    pattern_matches = re.findall(test_pattern, output)
    log_update(f"[PDB] Test name: {test_name}")
    log_update(f"[PDB] Matches: {pattern_matches}")
    log_update(f"[PDB] Output line: {op_line}")
    # Set all values to None if the pattern is not found

    micros_per_op = ops_per_sec = total_seconds = total_operations = data_speed = (
        data_speed_unit
    ) = None


    # Extract the performance metrics if the pattern is found
    for pattern_match in pattern_matches:
        # Convert each captured group to the appropriate type (float or int)
        micros_per_op = float(pattern_match[0])
        ops_per_sec = int(pattern_match[1])
        total_seconds = float(pattern_match[2])
        total_operations = int(pattern_match[3])
        # Check for specific workloads to handle additional data

        if "readrandomwriterandom" in output:
            data_speed = ops_per_sec
            data_speed_unit = "ops/sec"
            reads_found = None
        elif "jsonconfigured" in output:
            data_speed = ops_per_sec
            data_speed_unit = "ops/sec"
        elif "fillrandom" in output:
            data_speed = float(pattern_match[4])
            data_speed_unit = pattern_match[5]
            writes_data = {
                "count": int(pattern_match[6]),
                "average": float(pattern_match[7]),
                "std_dev": float(pattern_match[8]),
                "min": int(pattern_match[9]),
                "median": float(pattern_match[10]),
                "max": int(pattern_match[11]),
                "percentiles": {
                    "P50": float(pattern_match[12]),
                    "P75": float(pattern_match[13]),
                    "P99": float(pattern_match[14]),
                    "P99.9": float(pattern_match[15]),
                    "P99.99": float(pattern_match[16])
                }
            }
        elif "readrandom" in output:
            data_speed = float(pattern_match[4])
            data_speed_unit = pattern_match[5]
            reads_found = {
                "count": int(pattern_match[6]),
                "total": int(pattern_match[7])
            }
            reads_data = {
                "count": int(pattern_match[8]),
                "average": float(pattern_match[9]),
                "std_dev": float(pattern_match[10]),
                "min": int(pattern_match[11]),
                "median": float(pattern_match[12]),
                "max": int(pattern_match[13]),
                "percentiles": {
                    "P50": float(pattern_match[14]),
                    "P75": float(pattern_match[15]),
                    "P99": float(pattern_match[16]),
                    "P99.9": float(pattern_match[17]),
                    "P99.99": float(pattern_match[18]),
                },

            }
        elif "readwhilewriting" in output:
            data_speed = float(pattern_match[4])
            data_speed_unit = pattern_match[5]
            # reads_found = {
            #     "count": int(pattern_match[6]),
            #     "total": int(pattern_match[7])
            # }
            # reads_data = {
            #     "count": int(pattern_match[8]),
            #     "average": float(pattern_match[9]),
            #     "std_dev": float(pattern_match[10]),
            #     "min": int(pattern_match[11]),
            #     "median": float(pattern_match[12]),
            #     "max": int(pattern_match[13]),
            #     "percentiles": {
            #         "P50": float(pattern_match[14]),
            #         "P75": float(pattern_match[15]),
            #         "P99": float(pattern_match[16]),
            #         "P99.9": float(pattern_match[17]),
            #         "P99.99": float(pattern_match[18])
            #     }
            # }
        elif "mixgraph" in output:
            data_speed = ops_per_sec
            data_speed_unit = "ops/sec"
        else:
            log_update(f"[PDB] Test name not found in output: {output}")
            data_speed = ops_per_sec
            data_speed_unit = "ops/sec"
            log_update(
            f"[PDB] Ops per sec: {ops_per_sec} Total seconds: {total_seconds} Total operations: {total_operations} Data speed: {data_speed} {data_speed_unit}"
        )

    ops_per_sec_points = re.findall(
        "and \((.*),.*\) ops\/second in \(.*,(.*)\)", output
    )


    # Store all extracted values in a dictionary
    parsed_data = {
        "entries": entries,
        "micros_per_op": micros_per_op,
        "ops_per_sec": ops_per_sec,
        "total_seconds": total_seconds,
        "total_operations": total_operations,
        "data_speed": data_speed,
        "data_speed_unit": data_speed_unit,
        "ops_per_second_graph": [
            [float(a[1]) for a in ops_per_sec_points],
            [float(a[0]) for a in ops_per_sec_points],
        ],

    }

    # Grab the latency and push into the output logs file
    latency = re.findall("Percentiles:.*", output)
    for i in latency:
        log_update("[PDB] " + i)

    # Return the dictionary with the parsed data
    return parsed_data



def generate_db_bench_command_node(
    db_bench_path,
    database_path,
    options,
    run_count,
    test_name,
    file_path,
    db_bench_extra_args=[],
):
    """

    Generate the DB bench command

    Parameters:
    - db_bench_path (str): The path to the db_bench executable
    - database_path (str): The path to the database
    - option_file (dict): The options file to be used
    - run_count (str): The current iteration of the benchmark
    - test_name (str): The name of the test
    - db_bench_extra_args (list): Extra arguments to be passed to db_bench

    Returns:
    - list: The db_bench command
    """


    db_bench_command = [
        db_bench_path,
        f"--db={database_path}",
        f"--options_file={file_path}",
        "--use_direct_io_for_flush_and_compaction",
        "--use_direct_reads",
        "--compression_type=none",
        "--histogram",
        f"--dynamic_options_file=/tmp/mmap_file.mmap" if DYNAMIC_OPTION_TUNING else "",
        f"--threads={NUM_THREADS}",
        f"--trace_file={database_path}/tracefile",
        f"--num={NUM_ENTRIES}",
        f"--duration={DURATION}",

    ]

    # Preload phase - Only needed for some tests - Theoritically, mentioning test name should not be needed
    # However, I trust I will forget this in the future and this will act as a secondary measure
    if test_name == "readrandom" or test_name == "mixgraph" or test_name == "tracefile":
        if PRE_LOAD_DB_PATH != "":
            log_update("[SPM] Running Pre-load command")
            print("[SPM] Running Pre-load command")
            tmp_runner_rm = ["rm", "-rf", database_path]
            tmp_proc_rm = subprocess.run(tmp_runner_rm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
            tmp_runner = ["cp", "-r", PRE_LOAD_DB_PATH, database_path]
            tmp_proc = subprocess.run(tmp_runner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


    if test_name == "fillrandom":
        db_bench_command.append("--benchmarks=fillrandom")
    elif test_name == "readrandomwriterandom":
        db_bench_command.append("--benchmarks=readrandomwriterandom")

    elif test_name == "ycsbworkloadzipfian":
        # tmp_runner = db_bench_command[:-3] + ["--num=5000000", "--benchmarks=fillrandom", "--max_background_jobs=8", "--value_size=1000"]
        # tmp_proc = subprocess.run(tmp_runner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        db_bench_command.append("--benchmarks=ycsbworkloadzipfian")
        db_bench_command.append("--value_size=1000")
        db_bench_command.append("--use_existing_db")
    elif test_name == "readrandom":
        if PRE_LOAD_DB_PATH == "":
            log_update("[SPM] Running fillrandom to load the database")
            print("[SPM] Running fillrandom to load the database")

            tmp_runner = db_bench_command[:-3] + ["--num=50000000", "--benchmarks=fillrandom", "--max_background_jobs=8"]
            tmp_proc = subprocess.run(tmp_runner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        new_db_bench = db_bench_command + ["--benchmarks=readrandom", "--use_existing_db", "--reads=5000000"]
        db_bench_command = new_db_bench
    elif test_name == "mixgraph":
        if PRE_LOAD_DB_PATH == "":
            log_update("[SPM] Running fillrandom to load the database")
            print("[SPM] Running fillrandom to load the database")
            tmp_runner = db_bench_command[:-3] + ["--num=500000", "--benchmarks=fillrandom", "--key_size=48", "--value_size=43"]
            tmp_proc = subprocess.run(tmp_runner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        new_db_bench = db_bench_command[:-1] + ["--benchmarks=mixgraph", "--use_existing_db", f"--duration={DURATION}", 
                                                "--mix_get_ratio=0.83", "--mix_put_ratio=0.14", "--mix_seek_ratio=0.03", "--key_size=48",
                                                f"--sine_write_rate_interval_milliseconds={SINE_WRITE_RATE_INTERVAL_MILLISECONDS}", "--sine_mix_rate", 
                                                f"--sine_a={SINE_A}", f"--sine_b={SINE_B}", f"--sine_c={SINE_C}", f"--sine_d={SINE_D}"]

        db_bench_command = new_db_bench
    elif test_name == "readwhilewriting":
        db_bench_command.append("--benchmarks=readwhilewriting")
    elif test_name == "sinetest":
        db_bench_command += [

            "--benchmarks=fillrandom", "--sine_write_rate=true",
            f"--sine_write_rate_interval_milliseconds={SINE_WRITE_RATE_INTERVAL_MILLISECONDS}",
            f"--sine_a={SINE_A}", f"--sine_b={SINE_B}", f"--sine_c={SINE_C}", f"--sine_d={SINE_D}",
        ]
    elif test_name == "jsonconfigured":
        db_bench_command += [
            "--benchmarks=jsonconfigured", 
            f"--json_file_path={os.path.join(os.path.dirname(__file__), '../benchy.json')}"

        ]
    elif test_name == "tracefile":
        if PRE_LOAD_CMD != "" and PRE_LOAD_DB_PATH == "":
            tmp_runner = PRE_LOAD_CMD.split(" ")

            tmp_proc = subprocess.run(tmp_runner, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        db_bench_command[:-2] += [
            "--benchmarks=jsonconfigured", "--use_existing_db",
            f"--json_file_path={os.path.join(OUTPUT_PATH, 'trace_model.json')}"
        ]
    else:
        print(f"[SPM] Test name {test_name} not recognized")
        exit(1)

    db_bench_command += db_bench_extra_args

    log_update(f"[SPM] Command: {db_bench_command}")
    return db_bench_command


def store_db_bench_output(output_folder_name, output_file_name,
                          benchmark_results, options_file, reasoning, changed_value_dict):
    '''

    Store the output of db_bench in a file

    Parameters:
    - output_folder_name (str): Name of the folder to store the output file
    - output_file_name (str): Name of the output file
    - benchmark_results (dict): Dictionary containing the benchmark results
    - options_file (str): The options file used to generate the benchmark results
    - reasoning (str): The reasoning behind the options file

    Returns:
    - None

    '''
    with open(f"{output_folder_name}/{output_file_name}", "a+") as f:
        # Write benchmark results
        f.write("# " + json.dumps(benchmark_results) + "\n\n")
        
        # Write the options_file it self
        f.write(options_file + "\n")

        # Write the reasoning
        for line in reasoning.splitlines():
            f.write(f"# {line}\n")

        
        # Write the changed value
        if changed_value_dict is not None:
            f.write("\n# The changed values were:\n\n")
            for key, value in changed_value_dict.items():
                f.write(f"# {key}={value}\n")



def db_bench_node(db_bench_path, database_path, options, run_count, test_name, previous_throughput, options_files, file_path, db_bench_args=[], bm_iter=0):
    '''

    Store the options in a file
    Do the benchmark

    Parameters:
    - db_bench_path (str): The path to the db_bench executable
    - database_path (str): The path to the database
    - option_file (dict): The options file to be used
    - run_count (str): The current iteration of the benchmark

    Returns:
    - None

    '''
    global proc_out

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(options)
    # Perform pre-tasks to reset the environment
    pre_tasks(database_path, run_count)

    command = generate_db_bench_command_node(db_bench_path, database_path, options, run_count, test_name, file_path, db_bench_args)


    log_update(f"[SPM] Executing db_bench with command: {command}")
    print("[SPM] Executing db_bench")



    cgm = CGroupManager("llm_cgroup")
    cgm.create_cgroup()
    cgm.set_cpu_limit(2)
    cgm.set_memory_limit(4*1024*1024*1024)
    cgm.set_memory_swap_limit(4*1024*1024*1024)


    cgroup_monitor = CGroupMonitor("llm_cgroup")
    cgroup_monitor.start_monitoring()

    proc_out = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    cgm.add_process(proc_out.pid)
    stdout, stderr = proc_out.communicate()

    op = cgroup_monitor.stop_monitoring()
    avg_cpu_used = op["average_cpu_usage_percent"]
    avg_mem_used = op["average_memory_usage_percent"]

    print("[SPM] Finished running db_bench")
    print("---------------------------------------------------------------------------")

    
    return stdout, avg_cpu_used, avg_mem_used, options

def benchmark_runner(db_path, options, output_file_dir, reasoning, changed_value_dict, iteration_count, previous_results, options_files, db_bench_args, file_path):

    output, average_cpu_usage, average_memory_usage, options = db_bench_node(
        DB_BENCH_PATH, db_path, options, iteration_count, TEST_NAME, None, options_files, file_path, db_bench_args)


    # log_update(f"[SPM] Output: {output}")
    benchmark_results = parse_db_bench_output(output)

    # ERROR: Unable to load options file*
    if benchmark_results.get("error") is not None:
        is_error = True

        log_update(f"[SPM] Benchmark failed, the error is: {benchmark_results.get('error')}")
        print("[SPM] Benchmark failed, the error is: ",
              benchmark_results.get("error"))

    # ERROR: unexpected error
    elif benchmark_results['data_speed'] is None:
        is_error = True
        log_update(f"[SPM] Benchmark failed, the error is: Data speed is None. Check DB save path")
        print("[SPM] Benchmark failed, the error is: ",
              "Data speed is None. Check DB save path")

        # Save incorrect options in a file

    else:
        is_error = False


        log_update(f"[SPM] Latest result: {benchmark_results['data_speed']}"
                        f"{benchmark_results['data_speed_unit']} and {benchmark_results['ops_per_sec']} ops/sec.")
        log_update(f"[SPM] Avg CPU and Memory usage: {average_cpu_usage}% and {average_memory_usage}%")
        print(
            f"[SPM] Latest result: {benchmark_results['data_speed']}",
            f"{benchmark_results['data_speed_unit']} and {benchmark_results['ops_per_sec']} ops/sec.",
            f"\n[SPM] Avg CPU and Memory usage: {average_cpu_usage}% and {average_memory_usage}%"
        )
        text_output_for_visualization = (
            f"[SPM] Latest result: {benchmark_results['data_speed']}",
            f"{benchmark_results['data_speed_unit']} and {benchmark_results['ops_per_sec']} ops/sec.",
            f"\n[SPM] Avg CPU and Memory usage: {average_cpu_usage}% and {average_memory_usage}%",
        )
    output+= "\n"
    output += f"Avg CPU usage: {average_cpu_usage}%\n"
    output += f"Avg Memory usage: {average_memory_usage}%\n"
    return is_error, benchmark_results, average_cpu_usage, average_memory_usage, options, output, text_output_for_visualization


def get_executed_path(node):
    output_folder_dir = constants.OUTPUT_PATH
    os.makedirs(output_folder_dir, exist_ok=True)
    db_path = path_of_db() + f"/{node.id}"
    os.makedirs(db_path, exist_ok=True)
    return db_path


def summary_results(outputs):
    return summary_benchmark(outputs)

def benchmark(node_id, root):
    target_node = get_node_by_id(root, node_id)
    options = target_node.db_option

    reasoning = target_node.reasoning
    # commands = get_executed_commands(target_node)
    # options = get_node_options(target_node)

    output_folder_dir = constants.OUTPUT_PATH
    os.makedirs(output_folder_dir, exist_ok=True)
    db_path = path_of_db() + f"/{node_id}"
    os.makedirs(db_path, exist_ok=True)

    is_error, benchmark_results, average_cpu_usage, average_memory_usage, options, outputs, text_output_for_visualization = benchmark_runner(
            db_path, options, output_folder_dir, reasoning, None, 0, None, [], target_node.db_bench_option, target_node.file_path)
    if is_error:
        results = str(benchmark_results)
    else:
        # results = outputs
        results = str(benchmark_results) + "\n" + f"Avg CPU usage: {average_cpu_usage}%\n" + f"Avg Memory usage: {average_memory_usage}%\n"
        # results = summary_results(outputs)

    return results, text_output_for_visualization 


def benchmark_single_node(node):
    options = node.clean_options
    reasoning = node.reasoning

    output_folder_dir = constants.OUTPUT_PATH
    os.makedirs(output_folder_dir, exist_ok=True)
    db_path = path_of_db() + f"/{node.id}"
    os.makedirs(db_path, exist_ok=True)

    is_error, benchmark_results, average_cpu_usage, average_memory_usage, options, outputs = benchmark_runner(
            db_path, options, output_folder_dir, reasoning, None, 0, None, [], [], node.file_path)

    if is_error:
        results = benchmark_results
    else:
        # results = summary_results(outputs)
        results = benchmark_results


    return results 

