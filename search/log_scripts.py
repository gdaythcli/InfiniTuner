import re

def extract_metrics(log):
    metrics = {}

    # Extract throughput metrics from mixgraph line
    mixgraph_pattern = re.compile(
        r"mixgraph\s*:\s*([\d.]+)\s+micros/op\s+(\d+)\s+ops/sec\s+([\d.]+)\s+seconds\s+(\d+)\s+operations;\s+([\d.]+)\s+MB/s"
    )
    mixgraph_match = mixgraph_pattern.search(log)
    if mixgraph_match:
        metrics['micros_per_op'] = float(mixgraph_match.group(1))
        metrics['ops_sec'] = int(mixgraph_match.group(2))
        metrics['duration_sec'] = float(mixgraph_match.group(3))
        metrics['operations'] = int(mixgraph_match.group(4))
        metrics['mb_per_sec'] = float(mixgraph_match.group(5))

    # Extract average CPU and Memory usage
    cpu_pattern = re.compile(r"Avg CPU usage:\s*([\d.]+)%")
    mem_pattern = re.compile(r"Avg Memory usage:\s*([\d.]+)%")
    cpu_match = cpu_pattern.search(log)
    mem_match = mem_pattern.search(log)
    if cpu_match:
        metrics['avg_cpu_usage'] = float(cpu_match.group(1))
    if mem_match:
        metrics['avg_memory_usage'] = float(mem_match.group(1))

    # Extract average latency metrics from "Microseconds per ..." sections
    read_pattern = re.compile(r"Microseconds per read:\s*Count:\s*\d+\s+Average:\s*([\d.]+)")
    write_pattern = re.compile(r"Microseconds per write:\s*Count:\s*\d+\s+Average:\s*([\d.]+)")
    seek_pattern = re.compile(r"Microseconds per seek:\s*Count:\s*\d+\s+Average:\s*([\d.]+)")

    read_match = read_pattern.search(log)
    write_match = write_pattern.search(log)
    seek_match = seek_pattern.search(log)

    if read_match:
        metrics['avg_read_latency'] = float(read_match.group(1))
    if write_match:
        metrics['avg_write_latency'] = float(write_match.group(1))
    if seek_match:
        metrics['avg_seek_latency'] = float(seek_match.group(1))

    return metrics

if __name__ == "__main__":
    extracted = extract_metrics(log_data)
    print("Extracted Metrics:")
    for key, value in extracted.items():
        print(f"{key}: {value}")