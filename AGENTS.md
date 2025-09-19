# Repository Guidelines

## Project Structure & Module Organization
InfiniTuner orchestration lives in `main.py`, which wires Monte-Carlo tree search, benchmarking, and GPT-driven option generation. Core logic sits in `search/` (MCTS nodes, benchmark runner, logs) and `rocksdb/` (wrappers around `db_bench`, parsing, fine-tuning). Tuning artifacts and schema definitions reside in `options_files/` and `data_model/`, while prompt flows live in `gpt/`. Utilities such as cgroup helpers, system probes, and plotting are under `utils/`, and trace processing is isolated in `trace_analyzer/`. Use `docker/` only when batching device experiments via containerized runs.

## Build, Test, and Development Commands
- Create a virtual environment and install tooling: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Expand and compile RocksDB dependencies before first run: `tar -xzf v8.8.1.tar.gz && (cd rocksdb-8.8.1 && make -j"$(nproc)" static_lib db_bench trace_analyzer)`.
- Prime environment variables in `.env` (e.g., `OPENAI_API_KEY`) and verify reachable binaries via `python main.py --help`.
- Sanity-check new option files before benchmarking with `python check_missing_keys.py`.

## Coding Style & Naming Conventions
Python code follows PEP 8 with four-space indentation and descriptive snake_case naming. Run `black .` (23.x pinned in `requirements.txt`) before committing; keep imports standard-library-first and prefer type hints, as seen in `data_model/`. Configuration constants belong in `utils/constants.py`; resist hard-coding paths elsewhere.

## Testing Guidelines
There is no standalone unit suite; contributors should stage functional runs using minimal iterations: `python main.py --iteration_count 1 --case 1 --device data`. Capture benchmark outputs from `output/` and compare score deltas when adjusting search heuristics. When altering option schemas, regenerate validation via `check_missing_keys.py` and ensure `rocksdb/parse_db_bench_output.py` still parses updated fields. Include hardware context (CPU, storage type) in test notes because results depend on host characteristics.

## Commit & Pull Request Guidelines
Maintain concise, imperative commit titles similar to the existing history (e.g., `Refine MCTS scoring`). Provide context-rich bodies when touching benchmarking paths or sudo-reliant helpers. Pull requests should: describe the tuning scenario exercised, list commands run, attach key logs (trimmed) from `output/`, and link any tracking issues. Request review from maintainers before modifying `docker/` or `utils/root_cgroup_helper.sh`, as these affect privileged execution.

## Security & Configuration Tips
Never commit `.env`, API keys, or generated option dumps. Follow the README instructions for granting passwordless access to `utils/root_cgroup_helper.sh`, and document any sudoers edits in the PR. Validate that `utils/constants.py` paths match your filesystem before running long benchmarks to avoid filling unintended volumes.
