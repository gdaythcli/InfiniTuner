import json
import random
from collections import defaultdict
# from sklearn.cluster import KMeans
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Record:
    id: str
    content: Dict[str, Any]
    changed_options: List[str]
    summary: str

@dataclass
class Insight:
    id: str
    content: str
    source: str
    confidence: float

@dataclass
class Example:
    id: str
    content: Dict[str, Any]
    relevance_score: float


class Memory:
    def __init__(self):
        # Level 1: records store basic items
        self.records = []
        # Level 2: insights store extracted insight items
        self.insights = []
        # Level 3: examples store example items
        self.examples = []

    # ================================
    # LEVEL 1: RECORDS OPERATIONS
    # ================================
    
    def load_records_from_txt(self, file_path):
        """
        Load records from a text file.
        The file should contain lines starting with flags:
          - "Changed Options:" followed by a JSON string representing changed options.
          - "Summary:" followed by a summary string.
        Other lines are assumed to be JSON records.
        """
        """Load records from text file with flags"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    data = json.loads(line.strip())
                    record = Record(
                        id=data['id'],
                        content=data['content'],
                        changed_options=data['changed_options'],
                        summary=data['summary']
                    )
                    self.records.append(record)
        except Exception as e:
            print(f"Error loading records from txt: {e}")

    
    def load_records_from_tree(self, tree_data):
        """
        Load records from a tree structure.
        A recursive traversal will add all non-dict/non-list items as records.
        """
        try:
            def traverse(node):
                if isinstance(node, dict):
                    record = Record(
                        id=node.get('id'),
                        content=node.get('content', {}),
                        changed_options=node.get('changed_options', []),
                        summary=node.get('summary', '')
                    )
                    self.records.append(record)
                    for child in node.get('children', []):
                        traverse(child)
            
            traverse(tree_data)
        except Exception as e:
            print(f"Error loading records from tree: {e}")

    def load_insights_from_txt(self, file_path):
        """
        Load insights from a text file.
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    data = json.loads(line.strip())
                    insight = Insight(
                        id=data['id'],
                        content=data['content'],
                        source="RocksDB",
                        confidence=data['confidence']
                    )
                    self.insights.append(insight)
        except Exception as e:
            print(f"Error loading positive insights from txt: {e}")

    def cluster_records(self, k):
        """
        Cluster records into k clusters based on the numeric features in 'changed_options'.
        Each record should contain a 'changed_options' key with a dict of numerical values.
        Returns a dict mapping cluster labels to lists of records.
        should create a templet for LLM to cluster records
        """
        # Extract features from records that contain 'changed_options'
        features = []
        valid_indices = []
        for idx, record in enumerate(self.records):
            if "changed_options" in record and isinstance(record["changed_options"], dict):
                # Convert the changed_options dict into a list of values.
                features.append(list(record["changed_options"].values()))
                valid_indices.append(idx)

        if len(features) < k or not features:
            # Not enough records with valid features, return all records as one cluster.
            return {0: self.records}

        # Perform KMeans clustering on the extracted features.
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(features)

        clusters = defaultdict(list)
        for label, rec_index in zip(labels, valid_indices):
            clusters[label].append(self.records[rec_index])
        
        return clusters

    def insert_record(self, record):
        """Insert a new record"""
        try:
            self.records.append(record)
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False

    def update_record(self, record_id, updated_data):
        """Update an existing record"""
        try:
            for record in self.records:
                if record.id == record_id:
                    for key, value in updated_data.items():
                        setattr(record, key, value)
                    return True
            return False
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    def delete_record(self, record_id):
        """Delete a record"""
        try:
            self.records = [r for r in self.records if r.id != record_id]
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False

    def search_records(self, condition):
        """
        Return all records that satisfy the condition.
        'condition' should be a function that takes a record and returns True or False.
        """
        return [rec for rec in self.records if condition(rec)]

    # ================================
    # LEVEL 2: INSIGHTS OPERATIONS
    # ================================
    
    def get_insights_from_cluster(self, cluster):
        """Generate insights from a single cluster"""
        insights = []
        try:
            # Analyze common patterns in the cluster
            common_options = set.intersection(*[set(r.changed_options) for r in cluster])
            if common_options:
                insight = Insight(
                    id=f"cluster_insight_{len(self.insights)}",
                    content=f"Common changes: {', '.join(common_options)}",
                    source="cluster_analysis",
                    confidence=0.8
                )
                insights.append(insight)
        except Exception as e:
            print(f"Error generating cluster insights: {e}")
        return insights

    def get_insights_across_clusters(self, clusters):
        """Generate insights by comparing clusters"""
        insights = []
        try:
            for i, cluster1 in enumerate(clusters):
                for j, cluster2 in enumerate(clusters[i+1:], i+1):
                    # Compare clusters and generate insights
                    c1_options = set.union(*[set(r.changed_options) for r in cluster1])
                    c2_options = set.union(*[set(r.changed_options) for r in cluster2])
                    diff_options = c1_options.symmetric_difference(c2_options)
                    if diff_options:
                        insight = Insight(
                            id=f"cross_cluster_insight_{len(self.insights)}",
                            content=f"Distinct changes between clusters {i} and {j}: {', '.join(diff_options)}",
                            source="cross_cluster_analysis",
                            confidence=0.7
                        )
                        insights.append(insight)
        except Exception as e:
            print(f"Error generating cross-cluster insights: {e}")
        return insights

    def get_insights_from_random_records(self, n=5):
        """Generate insights from random records"""
        try:
            if self.records:
                sample = random.sample(self.records, min(n, len(self.records)))
                for record in sample:
                    insight = Insight(
                        id=f"random_insight_{len(self.insights)}",
                        content=f"summary: {record.summary}",
                        source="random_sampling",
                        confidence=0.5
                    )
                    self.insights.append(insight)
        except Exception as e:
            print(f"Error generating random insights: {e}")

    def get_insights_from_tree_trajectory(self, tree_data):
        """Generate insights from tree trajectory"""
        insights = []
        try:
            def analyze_path(node, path=[]):
                if isinstance(node, dict):
                    current_path = path + [node.get('id')]
                    if len(current_path) > 1:
                        insight = Insight(
                            id=f"trajectory_insight_{len(self.insights)}",
                            content=f"Path trajectory: {' -> '.join(current_path)}",
                            source="tree_trajectory",
                            confidence=0.6
                        )
                        insights.append(insight)
                    for child in node.get('children', []):
                        analyze_path(child, current_path)
            
            analyze_path(tree_data)
        except Exception as e:
            print(f"Error generating tree trajectory insights: {e}")
        return insights

    def insert_insight(self, insight):
        """Insert a new insight"""
        try:
            self.insights.append(insight)
            return True
        except Exception as e:
            print(f"Error inserting insight: {e}")
            return False        

    def upvote(self, index):
        """Upvote an insight"""
        try:
            for insight in self.insights:
                if insight.id == index:
                    insight.confidence += 0.1
                    return True
            return False
        except Exception as e:
            print(f"Error upvoting insight: {e}")
            return False
        
    def downvote(self, index):
        """Downvote an insight"""
        try:
            for insight in self.insights:
                if insight.id == index:
                    insight.confidence -= 0.1
                    return True
            return False
        except Exception as e:
            print(f"Error downvoting insight: {e}")
            return False
        
    def add(self, index, content, property):
        """Add a new insight"""
        try:
            insight = Insight(
                id=index,
                content=content,
                source=property,
                confidence=0.7
            )
            self.insights.append(insight)
            return True
        except Exception as e:
            print(f"Error adding insight: {e}")
            return False


    def return_insights(self):
        """
        Return all insights that satisfy the condition.
        """
        return self.insights

    # ================================
    # LEVEL 3: EXAMPLES OPERATIONS
    # ================================
    
    def load_examples_from_txt(self, file_path):
        """
        Load examples from a text file.
        Assumes the entire file is a valid JSON array of examples.
        """
        with open(file_path, "r") as f:
            try:
                examples_data = json.load(f)
                self.examples.extend(examples_data)
            except json.JSONDecodeError:
                # Handle error if file is not in the correct JSON format.
                pass

    def load_examples_from_tree(self, tree_examples):
        """
        Load examples from a tree structure.
        Every non-dict/non-list element encountered is added as an example.
        """
        def traverse(node):
            if isinstance(node, dict):
                for value in node.values():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
            else:
                self.examples.append(node)
        traverse(tree_examples)

    def chunk_examples(self, chunk_size):
        """
        Split the examples into chunks of a specified size.
        Returns a list of chunks.
        """
        return [self.examples[i:i + chunk_size] for i in range(0, len(self.examples), chunk_size)]
    
    def search_top_k_insights(self, k):
        """
        Retrieve the top k insights based on some ranking.
        For this example, we'll simply sort by the confidence score and return the k highest.
        """
        sorted_insights = sorted(self.insights, key=lambda ins: ins.confidence, reverse=True)
        return sorted_insights[:k]

    def search_top_k_examples(self, k):
        """
        Retrieve the top k examples based on some ranking.
        For this example, we'll simply sort by the string length of the example (converted to str)
        and return the k examples with the longest string representation.
        """
        sorted_examples = sorted(self.examples, key=lambda ex: len(str(ex)), reverse=True)
        return sorted_examples[:k]

    def insert_example(self, example):
        self.examples.append(example)

    def update_example(self, index, new_example):
        if 0 <= index < len(self.examples):
            self.examples[index] = new_example

    def delete_example(self, index):
        if 0 <= index < len(self.examples):
            del self.examples[index]

    def search_examples(self, condition):
        """
        Return all examples that satisfy the condition.
        """
        return [ex for ex in self.examples if condition(ex)]

    # ================================
    # MAIN FUNCTION
    # ================================

    def search(self, m, n):
        """
        The main function performs:
          - Clustering of records based on 'changed_options'
          - Extraction of insights from across clusters
          - Retrieval of the top k examples
        Returns a tuple: (top k insights, top k examples)
        """
        # Cluster records into k clusters.
        # clusters = self.cluster_records(k)
        # Get insights from clusters.
        # insights_by_cluster = self.get_insights_across_clusters(clusters)
        # For the sake of a simple "top k insights", we merge all cluster insights.
        # merged_insights = [insight for insight_list in insights_by_cluster.values() for insight in insight_list]
        # Get top k insights.
        top_insights = self.search_top_k_insights(m)
        # Get top k examples.
        top_examples = self.search_top_k_examples(n)
        return top_insights, top_examples


# ================================
# Example Usage:
# ================================
if __name__ == "__main__":
    memory = Memory()
    
    # For demonstration, we'll simulate loading records and examples.
    # In a real scenario, provide file paths or tree data structures.
    
    # Simulated file content for records (as if read from a txt file):
    # The file is expected to have flags "Changed Options:" and "Summary:".
    # simulated_record_lines = [
    #     'Changed Options: {"option1": 5, "option2": 10}',
    #     'Summary: This is a summary for all following records.',
    #     '{"id": 1, "data": "Record 1"}',
    #     '{"id": 2, "data": "Record 2"}'
    # ]
    # Write simulated records to a file.
    # with open("records.txt", "w") as f:
    #     f.write("\n".join(simulated_record_lines))
    
    # Load records from the simulated text file.

    memory.load_records_from_txt("/home/alice/LLM-Trace-Auto-Tuning/search/records.txt")
    
    # Also simulate loading records from a tree structure.
    # tree_records = {
    #     "branch1": [
    #         {"id": 3, "data": "Record 3", "changed_options": {"option1": 7, "option2": 3}, "summary": "Record 3 summary"},
    #         {"id": 4, "data": "Record 4", "changed_options": {"option1": 2, "option2": 8}, "summary": "Record 4 summary"}
    #     ],
    #     "branch2": {"id": 5, "data": "Record 5", "changed_options": {"option1": 6, "option2": 4}, "summary": "Record 5 summary"}
    # }
    # memory.load_records_from_tree(tree_records)
    
    # Cluster records into 3 clusters.
    # clusters = memory.cluster_records(3)
    # print("Clusters from records:")
    # for cluster_id, recs in clusters.items():
    #     print(f"Cluster {cluster_id}: {[rec.get('id', rec) for rec in recs]}")
    
    # Get insights from random records (for example purposes)
    memory.get_insights_from_random_records(2)
    
    # Simulated file content for examples (as a JSON array)
    simulated_examples = [
        {"example_id": 1, "content": "Example content one."},
        {"example_id": 2, "content": "Another example content which is a bit longer."},
        {"example_id": 3, "content": "Short."}
    ]
    with open("examples.txt", "w") as f:
        json.dump(simulated_examples, f)
    
    # Load examples from the simulated text file.
    memory.load_examples_from_txt("examples.txt")
    
    # Also simulate loading examples from a tree structure.
    # tree_examples = {
    #     "set1": [
    #         {"example_id": 4, "content": "Tree example content one."},
    #         {"example_id": 5, "content": "Another tree example content, slightly longer than the previous one."}
    #     ]
    # }
    # memory.load_examples_from_tree(tree_examples)
    
    # Retrieve top 3 insights and top 3 examples using the main function.
    # memory.update()
    top_insights, top_examples = memory.search(3,5)
    
    print("\nTop insights (up to 3):")
    for insight in top_insights:
        print(insight)
    
    print("\nTop examples (up to 5):")
    for example in top_examples:
        print(example)