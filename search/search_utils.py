import json
from utils import constants
import os
from data_model.config import INIConfig

from data_model.db_bench_options import DBBenchOptions
from typing import Optional, List
from num2words import num2words

class Insight:
    def __init__(self, content, property, confidence):
        self.content = content  # The content of the insight
        self.property = property  # The property of the insight
        self.confidence = confidence  # The confidence of the insight
        self.id = id(self)  # Unique ID for the insight

class Node:
    """
    A node in a tree structure representing configuration options.
    Each node contains configuration data, performance metrics, and relationships to other nodes.
    """

    def __init__(
        self,
        full_option: str,
        reasoning: str,
        parent: Optional['Node']=None,
        children: Optional[List['Node']]=None,
        visits: int=0,
        score: Optional[str]=None,
        db_option: Optional[str]=None,
        db_bench_option: Optional[List[str]]=None,
        db_option_changes: Optional[INIConfig]=None,
        db_bench_changes: Optional[DBBenchOptions] =None,
    ):
        """
        Initialize a Node with configuration and relationship data.

        Args:
            full_option: Complete configuration string or object
            reasoning: Explanation string for this configuration
            parent: Parent Node object (None for root)
            children: List of child Node objects (empty list by default)
            visits: Number of times this node has been visited/evaluated
            score: Performance score (may be a string with evaluation results)
            db_option: Database option configuration
            db_bench_option: Database benchmark option configuration
            db_option_changes: Changes to database options from parent
            db_bench_changes: Changes to benchmark options from parent
        """
        self.full_option = full_option  # Complete configuration string
        self.db_option = db_option  # Database specific configuration
        self.db_option_changes = db_option_changes  # Changes made to database options
        self.db_bench_option = db_bench_option  # Database benchmark configuration
        self.db_bench_changes = db_bench_changes  # Changes made to benchmark options
        self.parent = parent  # Reference to parent node
        self.children = children if children is not None else []  # List of child nodes
        self.visits = visits  # Visit counter for search algorithms
        self.score = score  # Performance evaluation results
        self.reasoning = reasoning  # Explanation for this configuration
        self.id = id(self)  # Unique identifier for this node
        self.file_path = None  # Path to associated file, if any
        self.branch_reasons = []
        # self.clean_options = None  # Cleaned/processed version of options

    def add_branch_reason(self, branch_reason):
        self.branch_reasons.append(str(num2words(len(self.branch_reasons)+1, ordinal=True)) + " branching reason: \n" + branch_reason)
    
    def is_leaf(self):
        """
        Check if this node is a leaf node (has no children).

        Returns:
            bool: True if the node has no children, False otherwise
        """
        return len(self.children) == 0

    def add_child(self, child):
        """
        Add a child node to this node.

        Args:
            child: Node object to add as a child
        """
        self.children.append(child)

    def digest(self):
        """
        Generate a human-readable summary of this node.

        Returns:
            str: Formatted string with key node information
        """
        # Determine what to display for option based on available attributes
        option_display = (
            self.db_option_changes
            if self.db_option_changes is not None
            else self.full_option
        )

        digest = (
            "This is digest of the node: \n"
            f"Node ID: {self.id}\n"
            f"Changed Database Options: {option_display}\n"
            f"Changed Benchmark Options: {self.db_bench_changes}\n"
            f"Visit times: {self.visits}\n"
            f"Results: {self.score}\n"
            f"Reasoning: {self.reasoning}\n"
            f"Children count: {len(self.children)}"
        )
        return digest

    def digest_json(self):

        """
        Generate a JSON-serializable dictionary summary of this node.

        Returns:
            dict: Dictionary containing key node information
        """
        # Create a comprehensive JSON representation
        return {
            "unique_id": self.id,
            "parent_id": "None" if self.parent is None else self.parent.id,
            "database_option": self.full_option,
            "database_option_changes_from_parent": "FAIL" if self.db_option_changes is None else self.db_option_changes.model_dump_json(),
            "database_benchmark_option": self.db_bench_option,
            "database_benchmark_changes_from_parent": "FAIL" if self.db_bench_changes is None else self.db_bench_changes.model_dump_json(),
            "benchmark_content": {
                "task_name": getattr(constants, "TEST_NAME", "unknown"),
                "visit_count": self.visits,
                "benchmark_result": self.score,
            },
            "reasoning_summary": self.reasoning,
            "has_children": not self.is_leaf(),
            "branch_reasons": self.branch_reasons,
            "children_count": len(self.children),
        }

    def brief_digest_json(self):
        """
        Generate a JSON-serializable dictionary summary of this node.

        Returns:
            dict: Dictionary containing key node information
        """
        # Create a comprehensive JSON representation
        return {
            "unique_id": self.id,
            "parent_id": "None" if self.parent is None else self.parent.id,
            "database_option_changes_from_parent": "FAIL" if self.db_option_changes is None else self.db_option_changes.model_dump_json(),
            "database_benchmark_changes_from_parent": "FAIL" if self.db_bench_changes is None else self.db_bench_changes.model_dump_json(),
            "benchmark_content": {
                "task_name": getattr(constants, "TEST_NAME", "unknown"),
                "visit_count": self.visits,
                "benchmark_result": self.score,
            },
            "reasoning_summary": self.reasoning,
            "has_children": not self.is_leaf(),
            "branch_reasons": self.branch_reasons,
            "children_count": len(self.children),
        }    

def get_node_by_id(root, target_id):
    """
    Find a node with the exact `target_id` by checking all nodes in the tree.

    Args:
        root (Node): The root node to start the search.
        target_id (int): The unique ID of the node to search for.

    Returns:
        Node: The node with the matching ID, or None if not found.
    """
    if root.id == target_id:
        return root
    for child in root.children:
        result = get_node_by_id(child, target_id)
        if result:
            return result
    return None


def bfs_collect_digests(root):
    """
    Perform a BFS traversal to collect the digest of all nodes in the tree.

    Args:
        root (Node): The root node to start the traversal.

    Returns:
        list: A list of digests from all nodes in BFS order.
    """
    queue = [root]
    digests = []
    while queue:
        current_node = queue.pop(0)
        digests.append(current_node.digest())
        queue.extend(current_node.children)
    return digests


def bfs_collect_json_digests(root):
    """
    Perform a BFS traversal to collect the digest of all nodes in the tree.

    Args:
        root (Node): The root node to start the traversal.

    Returns:
        list: A list of digests from all nodes in BFS order.
    """
    queue = [root]
    digests = []
    while queue:
        current_node = queue.pop(0)
        digests.append(current_node.digest_json())
        queue.extend(current_node.children)
    return digests



def collect_records_from_tree(node, records_file_path):
    """
    Perform a DFS traversal to collect the records of all nodes in the tree.

    Args:
        node (Node): The root node to start the traversal.
        records_file_path (str): The file path to store the records.

    Returns:
        list: A list of records from all nodes in DFS order.
    """
    if not os.path.exists(records_file_path):
        with open(records_file_path, "w") as f:  # Creates an empty file
            pass  # No need to write anything, just ensures file is created
    with open(records_file_path, "a") as f:
        json_record = json.dumps(node.digest_json())
        f.write(json_record + "\n")
        for child in node.children:
            collect_records_from_tree(child, records_file_path)
