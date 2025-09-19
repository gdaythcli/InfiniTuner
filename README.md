# InfiniTuner
This project aims to determine the best configuration for RocksDB，CacheLib，MySQL InnoDB using the assistance of LLMs. The process is completely automated, with the user only needing to run their workload.

## Prerequisites
The following instructions are for Ubuntu 24.04 and require Python 3.6 or higher:  

Install dependencies
```bash
apt-get update && apt-get install -y build-essential libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev git python3 python3-pip wget fio 
```

Download the InfiniTuner and RocksDB repositories:
```bash
git clone https://github.com/gdaythcli/InfiniTuner.git
wget https://github.com/facebook/rocksdb/archive/refs/tags/v8.8.1.tar.gz
tar -xzf v8.8.1.tar.gz
```

Copy modified trace_analyzer and db_bench_tool to RocksDB
```bash
cp ./InfiniTuner/trace_analyzer/tools/* ./rocksdb-8.8.1/tools/
cp ./InfiniTuner/db_bench_dynamic_opts/* ./rocksdb-8.8.1/tools/
```

Setup InfiniTuner
```bash
cd ./InfiniTuner
pip install -r requirements.txt

cd ../rocksdb-8.8.1
make -j static_lib db_bench trace_analyzer
```

> **Important!!** The cgroup_manager.py script requires root privileges to run. To avoid running everything as root, you can follow the steps below:
```bash
sudo visudo
```
```bash
# Unless you know what you are doing, add the following line **as is** to the end of the file. It gives **all** users the ability to run the root_cgroup_helper.sh script without a password.
ALL ALL=(ALL) NOPASSWD:/path/to/InfiniTuner/utils/root_cgroup_helper.sh
```
  
## How to use
To run the tests, run the following command:

Go to LLM-Trace-Auto-Tuning repo folder
Create `.env` file
```bash
nano .env
```

and put your OpenAI API Key
```.env
OPENAI_API_KEY="sk-..."
```

Make sure the paths in `utils/constant.py` are correctly set for your system.  
Run main.py
```bash
python3 main.py
```
