from gpt.content_generator import *
import rocksdb.subprocess_manager as spm
import utils.constants as constants
from utils.utils import path_of_db, log_gpt_response
import os

import json
from search.benchmark_runner import benchmark
from options_files.ops_options_file import cleanup_options_file_node, cleanup_options_file_node_with_structured_change

from gpt.gpt_request import request_gpt_with_structured_output
from pydantic import BaseModel
from data_model.config import INIConfig, Action, ActionList, Insights, InsightsDecision, InsightsList
from data_model.decision import Decision
from search.search_utils import Node, Insight, bfs_collect_digests, get_node_by_id, collect_records_from_tree, bfs_collect_json_digests
from search.memory import Memory
from utils.color_logger import logger
from data_model.db_bench_options import DBBenchOptions
from data_model.utils import make_field_optional
import pickle

def invoke_llm_to_generate_children(current_option, current_db_bench_option, device_information, results, current_node):
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB configuration "
        "by optimizing their options file based on their System information and benchmark output. "
        "Only provide options files for rocksdb version 8.8.1. "
        "Direct IO will always be used for both flush and compaction. "
        "Additionally, compression type is set to none always."
        "Special Reminder: write_buffer_size lays in [CFOptions \"default\"] NOT in [DBOptions]"
        "Special Reminder: db_write_buffer_size lays in [DBOptions]"
        # "You should try your best to generate valid options in the parent format. "
        f"The Device information is: {device_information}. "
        f"The parent option file is: {current_option}. "
        f"The parent db_bench option file is: {current_db_bench_option}. "
        f"You can also modfiy the following db_bench options: {" ".join(list(DBBenchOptions.__annotations__.keys()))}"

    )
    one_shot_example = ""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "In order to meet the requirement of variable name, I have done these changed alias: "
            "<alias>"
            'CFOptions "default" -> CFOptions'
            'TableOptions/BlockBasedTable "default" -> TableOptionsBlockBasedTable'
            "</alias>"
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "DBBenchOptions("
            "    key_5=value_5"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "4. **key_5=value_5**: Reason5."
            "Summary of changes and reasons."
            "</example>"
        )

    user_contents = [
        (
            f"The benchmark results for the parent file are: {results}. "
            "Based on these information, first generate 3 potential promsing children of the given parent option file. "
            # "Each child should be a small change (smaller then 10 options) from the parent option file to improve my database performance. "
            "Each child file should in the same format as the options_file (but only give the changed value) to improve my database performance."
            "Each changed key should be placed in the correct section. "
            # "Based on these information generate a new file in the same format as the options_file (but only give the changed value) to improve my database performance"
            # "Enclose the each child changed options file in ```."
            "The changes must be kv pairs. "
            "Then enclose the reason for each child option file."
        )
    ]

    user_contents[-1] += one_shot_example

    # "First generate 3 potential promsing childs of the given parent option file. Each child should be a small change (smaller then 10 options) from the parent option file. "
    # "Then show the changed options in 3 child options in the same format as the parent option file, explaining the reason for each child. ")


    actions = request_gpt_with_structured_output(
        system_content, user_contents, None, ActionList, 0.1
    )

    # with open("/home/alice/LLM-Trace-Auto-Tuning/output/output_data/output_2025-01-22_12-34-55/gpt_response/response_1.txt", "r") as file:
    #     assistant_reply = file.read()
    # pattern = re.compile(r"```([\s\S]*?)```")
    # matches = pattern.findall(assistant_reply)
    assert len(actions.actions) == 3, "Expected exactly 3 child options."
    # Extract the child options and their reasoning
    nodes = []
    for action in actions.actions:
        # for debug only
        option_changed_json = action.changed_db_options.json()
        with open(
            os.path.join(
                os.path.dirname(constants.OPTIONS_FILE_DIR),
                f"{id(action.changed_db_options)}.json",
            ),
            "w",
        ) as f:
            f.write(option_changed_json)
            print(option_changed_json)

        option_changes = action.changed_db_options
        db_bench_option_changes = action.changed_db_bench_options
        reasoning = action.reason

        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        # full_option, reasoning, parent=None, children=None, visits=0, score=None,
        # db_option=None, db_bench_option=None, db_option_changes=None, db_bench_changes=None
        node = Node(
            full_option=None,
            reasoning=reasoning,
            parent=current_node,
            children=None,
            visits=0,
            score=None,
            db_option=None,
            db_bench_option=None,
            db_option_changes=option_changes,
            db_bench_changes=db_bench_option_changes,
        )
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = (
            cleanup_options_file_node_with_structured_change(
                option_changes,
                current_db_bench_option,
                os.path.join(base_dir, child_opt_file),
                db_bench_option_changes,
            )
        )
        node.full_option = clean_options_file
        node.db_bench_option = db_bench_args
        node.db_option = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes  # Example options

def invoke_llm_to_generate_children_with_insights(current_option, current_db_bench_option, device_information, results, current_node, insights):
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB configuration "
        "by optimizing their options file based on their System information and benchmark output. "
        "Only provide options files for rocksdb version 8.8.1. "
        "Direct IO will always be used for both flush and compaction. "
        "Additionally, compression type is set to none always."
        # "Special Reminder: write_buffer_size lays in [CFOptions \"default\"] NOT in [DBOptions]"
        # "Special Reminder: db_write_buffer_size lays in [DBOptions]"
        # "You should try your best to generate valid options in the parent format. "
        f"The insights are: {insights}. "
        f"The Device information is: {device_information}. "
        f"The parent option file is: {current_option}. "
        f"The parent db_bench option file is: {current_db_bench_option}. "
        f"You can also modfiy the following db_bench options: {" ".join(list(DBBenchOptions.__annotations__.keys()))}"

    )
    one_shot_example = ""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "In order to meet the requirement of variable name, I have done these changed alias: "
            "<alias>"
            'CFOptions "default" -> CFOptions'
            'TableOptions/BlockBasedTable "default" -> TableOptionsBlockBasedTable'
            "</alias>"
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "DBBenchOptions("
            "    key_5=value_5"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "4. **key_5=value_5**: Reason5."
            "Summary of changes and reasons."
            "</example>"
        )

    user_contents = [
        (
            f"The benchmark results for the parent file are: {results}. "
            "Based on these information, first generate 3 potential promsing children of the given parent option file. "
            # "Each child should be a small change (smaller then 10 options) from the parent option file to improve my database performance. "
            "Each child file should in the same format as the options_file (but only give the changed value) to improve my database performance."
            "Each changed key should be placed in the correct section. "
            # "Based on these information generate a new file in the same format as the options_file (but only give the changed value) to improve my database performance"
            # "Enclose the each child changed options file in ```."
            "The changes must be kv pairs. "
            "Then enclose the reason for each child option file."
        )
    ]

    user_contents[-1] += one_shot_example

    # "First generate 3 potential promsing childs of the given parent option file. Each child should be a small change (smaller then 10 options) from the parent option file. "
    # "Then show the changed options in 3 child options in the same format as the parent option file, explaining the reason for each child. ")


    actions = request_gpt_with_structured_output(
        system_content, user_contents, None, ActionList, 0.1
    )

    # with open("/home/alice/LLM-Trace-Auto-Tuning/output/output_data/output_2025-01-22_12-34-55/gpt_response/response_1.txt", "r") as file:
    #     assistant_reply = file.read()
    # pattern = re.compile(r"```([\s\S]*?)```")
    # matches = pattern.findall(assistant_reply)
    assert len(actions.actions) == 3, "Expected exactly 3 child options."
    # Extract the child options and their reasoning
    nodes = []
    for action in actions.actions:
        # for debug only
        option_changed_json = action.changed_db_options.json()
        with open(
            os.path.join(
                os.path.dirname(constants.OPTIONS_FILE_DIR),
                f"{id(action.changed_db_options)}.json",
            ),
            "w",
        ) as f:
            f.write(option_changed_json)
            print(option_changed_json)

        option_changes = action.changed_db_options
        db_bench_option_changes = action.changed_db_bench_options
        reasoning = action.reason

        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        # full_option, reasoning, parent=None, children=None, visits=0, score=None,
        # db_option=None, db_bench_option=None, db_option_changes=None, db_bench_changes=None
        node = Node(
            full_option=None,
            reasoning=reasoning,
            parent=current_node,
            children=None,
            visits=0,
            score=None,
            db_option=None,
            db_bench_option=None,
            db_option_changes=option_changes,
            db_bench_changes=db_bench_option_changes,
        )
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = (
            cleanup_options_file_node_with_structured_change(
                option_changes,
                current_db_bench_option,
                os.path.join(base_dir, child_opt_file),
                db_bench_option_changes,
            )
        )
        node.full_option = clean_options_file
        node.db_bench_option = db_bench_args
        node.db_option = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes  # Example options



def invoke_llm_with_insights(option, insights, device_information, results):
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB performance "
        "by optimizing their options file based on their System information and benchmark output. "
        "Direct IO will always be used for both flush and compaction. "
        "Additionally, compression type is set to none always."
        "You should try your best to generate valid options. DO NOT ADD NEW KEYS to each section. "
        f"The Device information is: {device_information}. "
        f"The parent option file is: {option}. "
        f"The insights are: {insights}. "
    )
    one_shot_example = ""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "Summary of changes and reasons."
            "</example>"
        )

    user_contents = [
        (
            f"The benchmark results for the parent file are: {results}. "
            "Based on these information, first generate 1 potential promsing children of the given parent option file. "
            "You should apply some changes (smaller then 10 options) from the parent option file to improve my database performance. "
            "Enclose the changed options file in ```."
            "The changes must be kv pairs. "
            "Then enclose the reason for changed option file."
        )
    ]
    user_contents[-1] += one_shot_example

    actions = request_gpt_with_structured_output(
        system_content, user_contents, None, ActionList, 0.1
    )

    assert len(actions.actions) == 1, "Expected exactly 1 options file."
    nodes = []
    for action in actions.actions:
        # for debug only
        changed_json = action.changed.json()
        with open(
            os.path.join(
                os.path.dirname(constants.OPTIONS_FILE_DIR),
                f"{id(action.changed)}.json",
            ),
            "w",
        ) as f:
            f.write(changed_json)
            print(changed_json)

        option = action.changed
        reasoning = action.reason
        node = Node(option=option, reasoning=reasoning)
        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = (
            cleanup_options_file_node_with_structured_change(
                option, [], os.path.join(base_dir, child_opt_file)
            )
        )
        node.clean_options = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes


def invoke_llm__with_insights_and_examples(
    option, insights, examples, device_information, results
):
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB performance "
        "by optimizing their options file based on their System information and benchmark output. "
        "Direct IO will always be used for both flush and compaction. "
        "Additionally, compression type is set to none always."
        "NOTE: write_buffer_size ONLY exists in CFOptions. "
        f"The Device information is: {device_information}. "
        f"The parent option file is: {option}. "
        f"The insights are: {insights}. "
        f"The examples are: {examples}. "
    )
    one_shot_example = ""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "In order to meet the requirement of variable name, I have done these chang alias: "
            "<alias>"
            'CFOptions "default" -> CFOptions'
            'TableOptions/BlockBasedTable "default" -> TableOptionsBlockBasedTable'
            "</alias>"
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "Summary of changes and reasons."
            "</example>"
        )

    user_contents = [
        (
            f"The benchmark results for the parent file are: {results}. "
            "Based on these information, please generate optimal options file. "
            "You should apply only small change (smaller then 10 options) from the parent option file to improve my database performance. "
            "Enclose the changed options file in ```."
            "The changes must be kv pairs. "
            "Then enclose the reason for changed option file."
        )
    ]
    user_contents[-1] += one_shot_example

    actions = request_gpt_with_structured_output(
        system_content, user_contents, None, ActionList, 0.1
    )

    assert len(actions.actions) == 1, "Expected exactly 1 options file."
    nodes = []
    for action in actions.actions:
        # for debug only
        changed_json = action.changed.json()
        with open(
            os.path.join(
                os.path.dirname(constants.OPTIONS_FILE_DIR),
                f"{id(action.changed)}.json",
            ),
            "w",
        ) as f:
            f.write(changed_json)
            print(changed_json)

        option = action.changed
        reasoning = action.reason
        node = Node(option=option, reasoning=reasoning)
        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = (
            cleanup_options_file_node_with_structured_change(
                option, [], os.path.join(base_dir, child_opt_file)
            )
        )
        node.clean_options = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes


def invoke_llm_with_insights(option, insights, device_information, results):
    system_content = (
    "You are a RocksDB Expert. "
    "You are being consulted by a company to help improve their RocksDB performance "
    "by optimizing their options file based on their System information and benchmark output. "
    "Direct IO will always be used for both flush and compaction. "
    "Additionally, compression type is set to none always."
    "You should try your best to generate valid options. "
    f"The Device information is: {device_information}. "
    f"The parent option file is: {option}. "
    f"The insights are: {insights}. "
    )
    one_shot_example=""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "Summary of changes and reasons."
            "</example>"
        )


    user_contents = [(
        f"The benchmark results for the parent file are: {results}. "
        "Based on these information, first generate 1 potential promsing children of the given parent option file. "
        "You should apply some changes (smaller then 10 options) from the parent option file to improve my database performance. " 
        "Enclose the changed options file in ```."
        "The changes must be kv pairs. "
        "Then enclose the reason for changed option file."
    )]
    user_contents[-1] += one_shot_example

    actions = request_gpt_with_structured_output(system_content, user_contents, None, ActionList, 0.4)

    assert len(actions.actions) == 1, "Expected exactly 1 options file."
    nodes = []
    for action in actions.actions:
        # for debug only
        changed_json = action.changed.json()
        with open(os.path.join(os.path.dirname(constants.OPTIONS_FILE_DIR), f"{id(action.changed)}.json"), "w") as f:
            f.write(changed_json)
            print(changed_json)


        option = action.changed
        reasoning = action.reason
        node = Node(option=option, reasoning=reasoning)
        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = cleanup_options_file_node_with_structured_change(option, [], os.path.join(base_dir, child_opt_file))
        node.clean_options = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes
    
def invoke_llm_with_insights_and_examples(option, insights, examples, device_information, results):
    system_content = (
    "You are a RocksDB Expert. "
    "You are being consulted by a company to help improve their RocksDB performance "
    "by optimizing their options file based on their System information and benchmark output. "
    "Direct IO will always be used for both flush and compaction. "
    "Additionally, compression type is set to none always."
    "You should try your best to generate valid options. "
    f"The Device information is: {device_information}. "
    f"The parent option file is: {option}. "
    f"The insights are: {insights}. "
    f"The examples are: {examples}. "
    )
    one_shot_example=""
    if constants.ENABLE_ONE_SHOT:
        one_shot_example = (
            "Here is an example of the format you should follow to generate optimal options: "
            "<example>"
            "INIConfig("
            "    Version=None,"
            "    DBOptions=['key_1=value_1', 'key_2=value_2'],"
            "    CFOptions=['key_3=value_3'],"
            "    TableOptionsBlockBasedTable=['key_4=value_4']"
            ")"
            "Briefly summarize the benchmark of current config. "
            "Key changes and reasons:"
            "1. **key_1=value_1**: Reason1."
            "2. **key_2=value_2**: Reason2."
            "3. **key_3=value_3**: Reason3."
            "4. **key_4=value_4**: Reason4."
            "Summary of changes and reasons."
            "</example>"
        )

    user_contents = [(
        f"The benchmark results for the parent file are: {results}. "
        "Based on these information, please generate optimal options file. "
        "You should apply only small change (smaller then 10 options) from the parent option file to improve my database performance. " 
        "Enclose the changed options file in ```."
        "The changes must be kv pairs. "
        "Then enclose the reason for changed option file."
    )]
    user_contents[-1] += one_shot_example

    actions = request_gpt_with_structured_output(system_content, user_contents, None, ActionList, 0.4)

    assert len(actions.actions) == 1, "Expected exactly 1 options file."
    nodes = []
    for action in actions.actions:
        # for debug only
        changed_json = action.changed.json()
        with open(os.path.join(os.path.dirname(constants.OPTIONS_FILE_DIR), f"{id(action.changed)}.json"), "w") as f:
            f.write(changed_json)
            print(changed_json)


        option = action.changed
        reasoning = action.reason
        node = Node(option=option, reasoning=reasoning)
        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        child_opt_file = f"{node.id}.ini"
        clean_options_file, changed_value_dict, db_bench_args = cleanup_options_file_node_with_structured_change(option, [], os.path.join(base_dir, child_opt_file))
        node.clean_options = clean_options_file
        node.file_path = os.path.join(base_dir, child_opt_file)
        nodes.append(node)

    return nodes

def run_benchmark(node_id, root):
    return benchmark(node_id, root)
    # options = node.clean_options
    # reasoning = node.reasoning
    # output_folder_dir = constants.OUTPUT_PATH
    # os.makedirs(output_folder_dir, exist_ok=True)
    # db_path = path_of_db() + f"/{node.id}"
    # os.makedirs(db_path, exist_ok=True)
    # is_error, benchmark_results, average_cpu_usage, average_memory_usage, options = spm.benchmark_mcts(
    #         db_path, options, output_folder_dir, reasoning, None, 0, None, [], [], node.file_path)
    # return benchmark_results  # Example score string

def ask_llm_to_evaluate_and_decide(root):
    """
    Simulates asking an LLM to evaluate the scores of nodes
    and decide the next node to explore.
    """
    # Example integration: You would send nodes' options and scores to the LLM
    tree_digest = bfs_collect_json_digests(root)
    tree_node_description = (
        "<description>"
        "This JSON file represents a tree structure where each node contains the following information: "
        "Node Unique ID, Database Option, Changes in Database Option from Parent, "
        "Database Benchmark Option, Changes in Database Benchmark Option from Parent, "
        "Benchmark Content (which includes Task Name, Visit Count, and Benchmark Score), "
        "Reasoning Summary, and Child Node Information (Has Children, Children Count). "
        "Each Node Unique ID uniquely identifies the node. "
        "The Database Option field specifies the configuration option used by the node, while "
        "Changes in Database Option from Parent indicates how this option has been modified compared to its parent node (marked as 'FAIL' if no change is detected). "
        "Similarly, the Database Benchmark Option and its corresponding changes field capture the benchmark-specific settings and any modifications from the parent. "
        "Benchmark Content provides detailed information about the benchmark task, including the task name, the number of visits, and the benchmark score. "
        "Reasoning Summary describes the rationale for extending this node from its parent, explaining why this particular branch is explored. "
        "Branch Reasons is a list of explanations that justify why the node branched out to create one or more child nodes, accommodating the possibility of multiple branching events. "
        "Finally, the Child Node Information specifies whether the node has any children and the total count of those child nodes. "
        "</description>"
    )
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB performance "
        "by optimizing their options file based on their System information and benchmark output. "
        "You are using MCTS to search for the best options file. "
        "You are given the whole search tree information. "
        f"The search tree information are shown in the following format: "
        f"Here is the description of the node structure :"
        f"{tree_node_description}"
        "We traverse the tree in BFS order. "
        f"Here are the whole search tree information: {tree_digest}. "
    )

    user_contents = [
        (
            "Based on these information, to improve the performance of system, please tell me which node you want to explore next. "
            "Please first give me the node ID of the node you want to explore next. "
            "Then give me the reason why you want to further explore this node. "
        )
    ]


    decision = request_gpt_with_structured_output(
        system_content, user_contents, None, Decision, 0.1
    )

    node = get_node_by_id(root, int(decision.node_id))
    reasoning = decision.action

    return node, reasoning

def ask_llm_to_evaluate_and_decide_with_insights(root, insights):
    """
    Simulates asking an LLM to evaluate the scores of nodes
    and decide the next node to explore.
    """
    # Example integration: You would send nodes' options and scores to the LLM
    tree_digest = bfs_collect_json_digests(root)
    tree_node_description = (
        "<description>"
        "This JSON file represents a tree structure where each node contains the following information: "
        "Node Unique ID, Database Option, Changes in Database Option from Parent, "
        "Database Benchmark Option, Changes in Database Benchmark Option from Parent, "
        "Benchmark Content (which includes Task Name, Visit Count, and Benchmark Score), "
        "Reasoning Summary, and Child Node Information (Has Children, Children Count). "
        "Each Node Unique ID uniquely identifies the node. "
        "The Database Option field specifies the configuration option used by the node, while "
        "Changes in Database Option from Parent indicates how this option has been modified compared to its parent node (marked as 'FAIL' if no change is detected). "
        "Similarly, the Database Benchmark Option and its corresponding changes field capture the benchmark-specific settings and any modifications from the parent. "
        "Benchmark Content provides detailed information about the benchmark task, including the task name, the number of visits, and the benchmark score. "
        "Reasoning Summary describes the rationale for extending this node from its parent, explaining why this particular branch is explored. "
        "Branch Reasons is a list of explanations that justify why the node branched out to create one or more child nodes, accommodating the possibility of multiple branching events. "
        "Finally, the Child Node Information specifies whether the node has any children and the total count of those child nodes. "
        "</description>"
    )
    system_content = (
        "You are a RocksDB Expert. "
        "You are being consulted by a company to help improve their RocksDB performance "
        "by optimizing their options file based on their System information and benchmark output. "
        "You are using MCTS to search for the best options file. "
        "You are given the whole search tree information. "
        f"The search tree information are shown in the following format: "
        f"Here is the description of the node structure :"
        f"{tree_node_description}"
        "We traverse the tree in BFS order. "
        f"Here are the whole search tree information: {tree_digest}. "
        "You are also given the insights. "
        f"The insights are: {insights}. "
    )

    user_contents = [
        (
            "Based on these information, to improve the performance of system, please tell me which node you want to explore next. "
            "Please first give me the node ID of the node you want to explore next. "
            "Then give me the reason why you want to further explore this node. "
        )
    ]


    decision = request_gpt_with_structured_output(
        system_content, user_contents, None, Decision, 0.1
    )

    node = get_node_by_id(root, int(decision.node_id))
    reasoning = decision.action

    return node, reasoning

def invoke_llm_to_collect_insights_from_records(records_file_dir):
    """
    Collect insights from the records file.
    """
    records = []
    with open(records_file_dir, "r") as file:
        records = file.readlines()
    records = [record.strip() for record in records if record.strip()]
    records = "\n".join(records)
    system_content = (
    "You are a RocksDB Expert. "
    "You are being consulted by a company to help improve their RocksDB performance "
    "by summarizing the high level insights from the testing records. "
    "You are given several records of RocksDB performance testing based on different option settings. "
    f"The records are: {records}. "
    )
    
    user_contents = [(
        "Based on these information, please tell me some tuning insights you can get from the records file. "
        "For each insight, include:"
        "1. Insight Content: A clear description of the tuning insight."
        "2. A property label:"
        "- 'positive' if the insight indicates improved performance or error-free operation."
        "- 'negative' if the insight indicates degraded performance, errors, or issues."
        "3. Explanation: A brief explanation of why the insight is classified as positive or negative."
        "4. Confidence Score: A numerical score between 0 and 1 that evaluates the significance of the insight."
        "For positive insights, a higher score indicates a stronger association with improved performance."
        "For negative insights, a higher score indicates that addressing this insight has a higher probability of preventing errors or performance degradation."
    )]

    insights = request_gpt_with_structured_output(system_content, user_contents, None, InsightsList,0.4)
    # store the insights in two files, positive and negative
    positive_insights = []
    negative_insights = []
    for insight in insights.insights:
        if insight.property == "positive":
            insight_obj = Insight(insight.content, "positive", insight.confidence)
            positive_insights.append(insight_obj)
        else:
            insight_obj = Insight(insight.content, "negative", insight.confidence)
            negative_insights.append(insight_obj)
    # Save positive insights
    with open(constants.POSITIVE_INSIGHTS_FILE_DIR, "a") as file:
        for insight in positive_insights:
            # Create a dictionary for the insight
            insight_dict = {
                "id": insight.id,
                "content": insight.content,
                "property": insight.property,
                "confidence": insight.confidence
            }
            # Write the JSON string followed by a newline
            file.write(json.dumps(insight_dict) + "\n")
    # Save negative insights
    with open(constants.NEGATIVE_INSIGHTS_FILE_DIR, "a") as file:
        for insight in negative_insights:
            # Create a dictionary for the insight
            insight_dict = {
                "id": insight.id,
                "content": insight.content,
                "property": insight.property,
                "confidence": insight.confidence
            }
            # Write the JSON string followed by a newline
            file.write(json.dumps(insight_dict) + "\n")

    return insights

def invoke_llm_for_insights_reflection_and_refine(memory, examples, records_file_dir):
    """
    Collect insights from the records file.
    """
    records = []
    with open(records_file_dir, "r") as file:
        records = file.readlines()
    records = [record.strip() for record in records if record.strip()]
    records = "\n".join(records)
    insights = memory.return_insights()
    system_content = (
    "You are a RocksDB Expert. "
    "You are reviewing the previous insights. Based on the latest testing records and examples"
    "Please decide three operations on insights: Upvote, Downvote, and Add."
    "Upvote any insights that have truly contributed to improved system performance" 
    "Downvote any insights that lead to worse performance, invoke errors, or are otherwise not helpful for performance tuning. "
    "Add any insights that can help further tune system performance. "
    "Your new insights should be 'positive' if the insight indicates improved performance or error-free operation."
    "Or 'negative' if the insight indicates degraded performance, errors, or issues."
    "Your new insights should reflect the current testing data."
    "You are given several records, examples of system performance testing based on different option settings. "
    f"The records are: {records}. "
    f"The examples are: {examples}. "
    "You are also given the previous insights. "
    f"The previous insights are: {insights}. "
    )

    user_contents = [(
        "Please tell me the decision you want to make for each insight with the following structure. "
        "For each insight, include:"
        "id <unique id for previous insights or 0 for new insights>"
        "operation <upvote | downvote | add>"
        "content <the content for new insight or empty for old insights>"
        "property <positive | negative>"
        "reason <the reason why you make this decision>"
    )]

    insights_decisions = request_gpt_with_structured_output(system_content, user_contents, None, InsightsDecision,0.4)
    # process each insight decision
    for insight_decision in insights_decisions.actions:
        if insight_decision.operation == "upvote":
            memory.upvote(insight_decision.id)
        elif insight_decision.operation == "downvote":
            memory.downvote(insight_decision.id)
        elif insight_decision.operation == "add":
            memory_insight_obj = Insight(insight_decision.content, insight_decision.property)
            memory.add(memory_insight_obj.id, memory_insight_obj.content, memory_insight_obj.property)
            # save the new insight to the file
            if insight_decision.property == "positive":
                insight_obj = Insight(insight_decision.content, "positive")
                # Create a dictionary for the insight
                insight_dict = {
                    "id": insight_obj.id,
                    "content": insight_obj.content,
                    "property": insight_obj.property
                }
                # Write the JSON string followed by a newline
                # Save positive insights
                with open(constants.POSITIVE_INSIGHTS_FILE_DIR, "a") as file:
                    file.write(json.dumps(insight_dict) + "\n")
            elif insight_decision.property == "negative":
                insight_obj = Insight(insight_decision.content, "negative")
                # Create a dictionary for the insight
                insight_dict = {
                    "id": insight_obj.id,
                    "content": insight_obj.content,
                    "property": insight_obj.property
                }
                # Write the JSON string followed by a newline
                # Save negative insights
                with open(constants.NEGATIVE_INSIGHTS_FILE_DIR, "a") as file:
                    file.write(json.dumps(insight_dict) + "\n")
        else:
            raise ValueError(f"Unknown operation: {insight_decision.operation}")


def mcts(root_option, reasoning, benchmark_results, device_information, max_iterations=3):
    root = Node(
        full_option=root_option,
        reasoning=reasoning,
        parent=None,
        children=[],
        visits=0,
        score=benchmark_results,
    )

    for it in range(max_iterations):
      
        # 1. Expand root by asking LLM to generate child nodes
        logger.info(f"Current iteration: {it}")
        if root.is_leaf():
            childs = invoke_llm_to_generate_children(
                root.full_option,
                root.db_bench_option,
                device_information,
                root.score,
                root,
            )
            for child in childs:
                child.parent = root
                root.add_child(child)

        # 2. Run benchmarks for all child nodes to generate score strings
        for child in root.children:
            logger.info(f"Processing child node: {child.id}")
            if child.visits == 0:  # Only process unvisited nodes

                child.score, child.text_output = run_benchmark(child.id, root)

                child.visits += 1
            else:
                child.visits += 1

        # for debugging
        # exit(1)
        # 3. Ask LLM to evaluate scores and decide the next node
        logger.info("Asking LLM to evaluate scores and decide the next node.")
        next_node, explore_reason = ask_llm_to_evaluate_and_decide(root)
        logger.info(f"Next node to explore: {next_node.id}")
        logger.info(f"Reason for exploring: {explore_reason}")
        # 4. Simulate visiting the chosen node
        next_node.visits += 1
        next_node.add_branch_reason(explore_reason)

        # Optionally, expand the chosen node by generating its children
        if next_node.is_leaf():
            childs = invoke_llm_to_generate_children(
                next_node.full_option,
                next_node.db_bench_option,
                device_information,
                next_node.score,
                next_node,
            )
            for child in childs:
                child.parent = next_node
                next_node.add_child(child)
        else:
            # If the chosen node is not a leaf, we can also benchmark its children
            for child in next_node.children:
                if child.visits == 0:  # Only process unvisited nodes
                    child.score, child.text_output = run_benchmark(child.id, root)
                    child.visits += 1
                else:
                    child.visits += 1


    
    # After all iterations, ask LLM to determine the best option overall
    best_node, explore_reason = ask_llm_to_evaluate_and_decide(root)
    collect_records_from_tree(root, constants.RECORDS_FILE_DIR)
    # Dump the tree
    base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
    with open(os.path.join(base_dir, "treedump.pkl"), "wb") as f:
        pickle.dump(root, f)
        

    invoke_llm_to_collect_insights_from_records(constants.RECORDS_FILE_DIR)

    return best_node

def insights_driven_mcts(option, reasoning, memory, device_information, results, max_iterations, refine_flag, insights_num, examples_num, refine_num):
    root = Node(full_option=option, reasoning=reasoning, parent=None, children=[], visits=0, score=results)
    best_node = None
    if refine_flag:
        for i in range(refine_num):
            insights, examples = memory.search(insights_num, examples_num)
            for _ in range(max_iterations):
                # 1. Expand root by asking LLM to generate child nodes
                if root.is_leaf():
                    childs = invoke_llm_to_generate_children_with_insights(root.full_option, root.db_bench_option, device_information, root.score, root, insights)
                    for child in childs:
                        child.parent = root
                        root.add_child(child)
                # 2. Run benchmarks for all child nodes to generate score strings
                for child in root.children:
                    logger.info(f"Processing child node: {child.id}")
                    if child.visits == 0:
                        child.score, child.text_output = run_benchmark(child.id, root)
                        child.visits += 1
                    else:
                        child.visits += 1
                # 3. Ask LLM to evaluate scores and decide the next node
                logger.info("Asking LLM to evaluate scores and decide the next node with insights.")
                next_node, explore_reason = ask_llm_to_evaluate_and_decide_with_insights(root, insights)
                # 4. Simulate visiting the chosen node
                next_node.visits += 1
                next_node.add_branch_reason(explore_reason)
                # Optionally, expand the chosen node by generating its children
                if next_node.is_leaf():
                    childs = invoke_llm_to_generate_children_with_insights(root.full_option, root.db_bench_option, device_information, root.score, root, insights)
                    for child in childs:
                        child.parent = next_node
                        next_node.add_child(child)
                else:
                    # If the chosen node is not a leaf, we can also benchmark its children
                    for child in next_node.children:
                        logger.info(f"Processing child node: {child.id}")
                        if child.visits == 0:
                            child.score, child.text_output = run_benchmark(child.id, root)
                            child.visits += 1
                        else:
                            child.visits += 1
            # After all iterations, ask LLM to determine the best option overall
            best_node, _ = ask_llm_to_evaluate_and_decide_with_insights(root, insights)
            collect_records_from_tree(root, constants.RECORDS_FILE_DIR)
            base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
            with open(os.path.join(base_dir, "treedump.pkl"), "wb") as f:
                pickle.dump(root, f)
            invoke_llm_for_insights_reflection_and_refine(memory, examples, constants.RECORDS_FILE_DIR)

    else:
        insights, examples = memory.search(insights_num, examples_num)
        for _ in range(max_iterations):
            # 1. Expand root by asking LLM to generate child nodes
            if root.is_leaf():
                childs = invoke_llm_to_generate_children_with_insights(root.full_option, root.db_bench_option, device_information, root.score, root, insights)
                for child in childs:
                    child.parent = root
                    root.add_child(child)
            # 2. Run benchmarks for all child nodes to generate score strings
            for child in root.children:
                logger.info(f"Processing child node: {child.id}")
                if child.visits == 0:
                    child.score, child.text_output = run_benchmark(child.id, root)
                    child.visits += 1
                else:
                    child.visits += 1
            # 3. Ask LLM to evaluate scores and decide the next node
            logger.info("Asking LLM to evaluate scores and decide the next node with insights.")
            next_node, explore_reason = ask_llm_to_evaluate_and_decide_with_insights(root, insights)
            # 4. Simulate visiting the chosen node
            next_node.visits += 1
            next_node.add_branch_reason(explore_reason)
            # Optionally, expand the chosen node by generating its children
            if next_node.is_leaf():
                childs = invoke_llm_to_generate_children_with_insights(root.full_option, root.db_bench_option, device_information, root.score, root, insights)
                for child in childs:
                    child.parent = next_node
                    next_node.add_child(child)
            else:
                # If the chosen node is not a leaf, we can also benchmark its children
                for child in next_node.children:
                    logger.info(f"Processing child node: {child.id}")
                    if child.visits == 0:
                        child.score, child.text_output = run_benchmark(child.id, root)
                        child.visits += 1
                    else:
                        child.visits += 1
        # After all iterations, ask LLM to determine the best option overall
        best_node, _ = ask_llm_to_evaluate_and_decide_with_insights(root, insights)
        collect_records_from_tree(root, constants.RECORDS_FILE_DIR)
        base_dir = os.path.dirname(constants.OPTIONS_FILE_DIR)
        with open(os.path.join(base_dir, "treedump.pkl"), "wb") as f:
            pickle.dump(root, f)
        invoke_llm_to_collect_insights_from_records(constants.RECORDS_FILE_DIR)

    return best_node


# if __name__ == "__main__":
#     invoke_llm_to_collect_insights_from_records()
#     best_option = mcts("Initial_Option", max_iterations=3)
#     print(f"The best option found: {best_option}")
