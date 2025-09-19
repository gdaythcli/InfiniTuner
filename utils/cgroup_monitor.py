import time
import os
import threading


class CGroupMonitor:
    def __init__(self, cgroup_name, cgroup_base_path="/sys/fs/cgroup"):
        self.cgroup_name = cgroup_name
        self.cgroup_base_path = cgroup_base_path
        self.cgroup_path = os.path.join(cgroup_base_path, cgroup_name)

        self.monitoring = False
        self.cpu_usage_percentages = []
        self.memory_usage = []
        self.monitor_thread = None
        self.start_time = None

    def get_cpu_usage_us(self):
        """Get the cumulative CPU usage in microseconds."""
        cpu_stat_path = os.path.join(self.cgroup_path, "cpu.stat")
        try:
            with open(cpu_stat_path, "r") as f:
                for line in f:
                    if line.startswith("usage_usec"):
                        usage_usec = int(line.split()[1])
                        return usage_usec
        except FileNotFoundError:
            pass
        return 0

    def get_cpu_limit(self):
        """Get the CPU quota and period."""
        cpu_max_path = os.path.join(self.cgroup_path, "cpu.max")
        try:
            with open(cpu_max_path, "r") as f:
                data = f.read().strip().split()
                if data[0] == "max":
                    return None, int(data[1])  # No quota, but we have the period
                else:
                    return int(data[0]), int(data[1])  # Quota and period in microseconds
        except FileNotFoundError:
            pass
        return None, 100000  # Default period if not specified

    def get_memory_usage(self):
        """Get the current memory usage in bytes."""
        memory_current_path = os.path.join(self.cgroup_path, "memory.current")
        try:
            with open(memory_current_path, "r") as f:
                return int(f.read().strip())
        except FileNotFoundError:
            pass
        return 0

    def get_memory_limit(self):
        """Get the memory limit in bytes."""
        memory_max_path = os.path.join(self.cgroup_path, "memory.max")
        try:
            with open(memory_max_path, "r") as f:
                return int(f.read().strip())
        except FileNotFoundError:
            pass
        return 0
    
    def get_swap_limit(self):
        """Get the swap limit in bytes."""
        swap_max_path = os.path.join(self.cgroup_path, "memory.swap.max")
        try:
            with open(swap_max_path, "r") as f:
                return int(f.read().strip())
        except FileNotFoundError:
            pass
        return

    def _monitor(self, interval):
        """Internal method to monitor CPU and memory usage."""
        previous_cpu_usage = self.get_cpu_usage_us()
        while self.monitoring:
            time.sleep(interval)

            # CPU percentage calculation
            current_cpu_usage = self.get_cpu_usage_us()
            delta_cpu_usage = current_cpu_usage - previous_cpu_usage
            previous_cpu_usage = current_cpu_usage

            quota, period = self.get_cpu_limit()
            num_cores = quota / period if quota else os.cpu_count()
            total_cpu_time_available = num_cores * (interval * 1000000)
            cpu_usage_percentage = (delta_cpu_usage / total_cpu_time_available) * 100

            # Store results
            self.cpu_usage_percentages.append(cpu_usage_percentage)
            self.memory_usage.append(self.get_memory_usage())

    def start_monitoring(self, interval=1):
        """Start monitoring CPU and memory usage."""
        if self.monitoring:
            raise RuntimeError("Monitoring is already running.")

        self.monitoring = True
        self.cpu_usage_percentages = []
        self.memory_usage = []
        self.start_time = time.time()
        self.monitor_thread = threading.Thread(target=self._monitor, args=(interval,), daemon=True)
        self.monitor_thread.start()

    def get_last_n_stats(self, n=1):
        """Get the last n stats recorded. Returns same format as stop_monitoring."""
        if not self.monitoring:
            raise RuntimeError("Monitoring is not running.")
        
        avg_cpu = sum(self.cpu_usage_percentages[-n:]) / n if self.cpu_usage_percentages else 0
        avg_memory = sum(self.memory_usage[-n:]) / n if self.memory_usage else 0
        avg_memory_gb = avg_memory / (1024 * 1024 * 1024)
        avg_memory_percent = (avg_memory / self.get_memory_limit()) * 100 if self.get_memory_limit() else 0

        max_cpu = max(self.cpu_usage_percentages[-n:], default=0)
        max_memory = max(self.memory_usage[-n:], default=0)
        max_memory_gb = max_memory / (1024 * 1024 * 1024)
        max_memory_percent = (max_memory / self.get_memory_limit()) * 100 if self.get_memory_limit() else 0

        return {
            "average_cpu_usage_percent": round(avg_cpu, 2),
            "average_memory_usage_gib": round(avg_memory_gb, 2),
            "average_memory_usage_percent": round(avg_memory_percent, 2),
            "max_cpu_usage_percent": round(max_cpu, 2),
            "max_memory_usage_gib": round(max_memory_gb, 2),
            "max_memory_usage_percent": round(max_memory_percent, 2)
        }

    def stop_monitoring(self):
        """Stop monitoring and return average and max usage stats."""
        if not self.monitoring:
            raise RuntimeError("Monitoring is not running.")

        self.monitoring = False
        self.monitor_thread.join()
        self.monitor_thread = None
        total_time = time.time() - self.start_time

        avg_cpu = sum(self.cpu_usage_percentages) / len(self.cpu_usage_percentages) if self.cpu_usage_percentages else 0
        avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        avg_memory_gb = avg_memory / (1024 * 1024 * 1024)
        avg_memory_percent = (avg_memory / self.get_memory_limit()) * 100 if self.get_memory_limit() else 0

        max_cpu = max(self.cpu_usage_percentages, default=0)
        max_memory = max(self.memory_usage, default=0)
        max_memory_gb = max_memory / (1024 * 1024 * 1024)
        max_memory_percent = (max_memory / self.get_memory_limit()) * 100 if self.get_memory_limit() else 0

        return {
            "average_cpu_usage_percent": round(avg_cpu, 2),
            "average_memory_usage_gib": round(avg_memory_gb, 2),
            "average_memory_usage_percent": round(avg_memory_percent, 2),
            "max_cpu_usage_percent": round(max_cpu, 2),
            "max_memory_usage_gib": round(max_memory_gb, 2),
            "monitoring_duration_s": round(total_time, 2),
            "max_memory_usage_percent": round(max_memory_percent, 2)
        }
