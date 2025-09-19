import os
import subprocess

class CGroupManager:
    def __init__(self, cgroup_name, cgroup_base_path="/sys/fs/cgroup"):
        self.cgroup_name = cgroup_name
        self.cgroup_base_path = cgroup_base_path
        self.cgroup_path = os.path.join(self.cgroup_base_path, cgroup_name)
        self.helper_script = os.path.join(os.path.dirname(__file__), "root_cgroup_helper.sh")

    def create_cgroup(self):
        """Create the cgroup."""
        if os.path.exists(self.cgroup_path):
            print(f"[CGM] Cgroup {self.cgroup_name} already exists.")
            return
        
        try:
            subprocess.run(["sudo", self.helper_script, "create", self.cgroup_path], check=True)
        except Exception as e:
            raise e

    def set_cpu_limit(self, quota):
        """Set the CPU quota. Assume period is default at 100000."""
        if quota < 100000:
            quota = quota * 100000
        cpu_max_path = os.path.join(self.cgroup_path, "cpu.max")
        subprocess.run(["sudo", self.helper_script, "write", cpu_max_path, str(quota)], check=True)

    def set_memory_limit(self, limit):
        """Set the memory limit in bytes."""
        memory_max_path = os.path.join(self.cgroup_path, "memory.max")
        subprocess.run(["sudo", self.helper_script, "write", memory_max_path, str(limit)], check=True)

    def set_memory_swap_limit(self, limit):
        """Set the memory+swap limit in bytes."""
        memory_swap_max_path = os.path.join(self.cgroup_path, "memory.swap.max")
        subprocess.run(["sudo", self.helper_script, "write", memory_swap_max_path, str(limit)], check=True)

    def add_process(self, pid):
        """Add a process to the cgroup."""
        proc_path = os.path.join(self.cgroup_path, "cgroup.procs")
        subprocess.run(["sudo", self.helper_script, "write", proc_path, str(pid)], check=True)

    def delete_cgroup(self):
        """Delete the cgroup."""
        subprocess.run(["sudo", self.helper_script, "delete", self.cgroup_path], check=True)