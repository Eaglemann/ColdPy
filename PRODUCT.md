Tool Name: ColdPy

Tagline / Description:
Analyze Python project startup performance and memory usage to identify slow or heavy imports. Suggest improvements to reduce cold start times for serverless, microservices, or large Python apps.

Summary:
ColdPy hooks into Python’s import system and runtime to measure import duration and memory footprint per module/package. It generates actionable reports highlighting “heavy hitters,” circular dependencies, and modules that could benefit from lazy loading. Optional visualization and CI integration make it production-relevant.

High-Level Goals

Measure real Python startup cost — runtime import time + memory usage.

Detect heavy or slow dependencies that impact cold start.

Provide actionable insights — suggest lazy loading, redundant imports, or refactors.

Support CI/CD integration — prevent regressions in startup performance.

Easy to use locally — works on any Python project with minimal configuration.

Functional Requirements

Project Scan

Scan all top-level Python modules in a project.

Measure per-module import time.

Measure memory usage for each import (via tracemalloc).

Reporting

Generate a CLI table with: module/package, import time, memory usage.

Optional JSON output for CI or automation.

Highlight top 10 slowest or heaviest imports.

Dependency Analysis

Map import graph: which module imports which.

Detect circular dependencies.

Identify modules that bring heavy transitive imports.

Suggestions

Flag candidates for lazy loading.

Optional recommendations: split imports, refactor, or remove unused dependencies.

Visualization (optional MVP+ feature)

Generate Graphviz/DOT file showing import dependency graph.

Color-code nodes by import time / memory.

CI Integration

Optional --ci flag to output machine-readable JSON.

Compare PR vs main branch and flag regressions in import time or memory.

Command-Line Interface
Example commands:

coldpy scan ./myproject
coldpy top 10
coldpy graph --output=deps.png
coldpy compare --branch pr_branch
Non-Functional Requirements

Fast execution (parallelize module scans if needed).

Safe: does not modify code or environment.

Cross-platform: Linux, macOS, Windows.

Python >=3.10 (take advantage of modern syntax + typing).

Minimal dependencies (Typer/Click for CLI, Rich optional for output).

Cache results locally to avoid repeated scans on large projects.

Constraints

Must not require changes to the target project.

Must handle projects using virtualenv, Poetry, or Conda without breaking.

Avoid executing arbitrary project code beyond imports.

Should not run destructive operations (no file deletion, DB writes).

Initial MVP can skip visualization and CI diff comparison; core scanning + report is sufficient.

Optional / Advanced Features (post-MVP)

Lazy import refactor suggestions

Automatically suggest moving heavy imports inside functions.

Branch comparison

Detect regressions in import time or memory between branches.

AI-assisted insights

Optional local LLM integration to explain why an import is heavy or suggest refactors.

Docker / Lambda analysis

Run scans in containerized environments for accurate cold start profiling.

Example CLI Output
Module                 Import Time(ms)   Memory(MB)   Notes
------------------------------------------------------------
pandas                 420              110          Heavy, consider lazy import
numpy                  310              85           Heavy, transitive imports
requests               120              15
myproject.api          50               5
...

Optional JSON output:

{
  "modules": [
    {"name": "pandas", "time_ms": 420, "memory_mb": 110, "suggestions": ["lazy import"]},
    {"name": "numpy", "time_ms": 310, "memory_mb": 85}
  ]
}
Project Structure (MVP)
coldpy/
├─ coldpy/
│  ├─ __main__.py       # CLI entrypoint
│  ├─ scanner.py        # import time + memory measurement
│  ├─ graph.py          # dependency graph builder (optional)
│  ├─ reporter.py       # CLI table, JSON output
│  ├─ utils.py
│  ├─ config.py         # optional settings, cache
├─ tests/
├─ pyproject.toml
└─ README.md

# MVP

MVP Goal

Fully functional import-time + memory profiler for Python projects.

CLI-first, fast, and outputs readable tables and JSON.

No optional AI or visualization yet — just the core value.

Weekend 1: Core Scan & Reporting
Step 1: Setup CLI

Use Typer for CLI.

Commands:

coldpy scan <path>        # scan project for import cost
coldpy top [N]            # show top N heaviest imports
coldpy json [file]         # output JSON report

Set up project structure (scanner.py, reporter.py, cli.py, __main__.py).

Step 2: Implement Import Scanner

Use importlib hooks or wrap __import__ to measure import duration.

Use tracemalloc to measure memory usage per module.

For MVP, scan all .py files in the given path.

Record results in a simple dictionary:

{
    "module_name": "pandas",
    "import_time_ms": 420,
    "memory_mb": 110
}
Step 3: Reporting

Use rich (optional) to print tables:

Columns: Module | Import Time (ms) | Memory (MB) | Notes

Sort by heaviest import.

Implement optional JSON output for CI:

coldpy scan ./myproject --json report.json
Step 4: Test

Try on a small project.

Verify:

Modules are detected correctly.

Import times and memory make sense.

Output is readable.

Weekend 2: Enhancements + MVP polish
Step 1: Top N Command

Implement coldpy top [N] to quickly see slowest imports.

Optional flag: --threshold 50ms to show only significant imports.

Step 2: Caching

Cache previous scans in .coldpy/cache.json for faster repeated runs.

Store: module, import time, memory, timestamp.

Step 3: Basic Suggestions

For any import taking >100ms or >50MB memory, add a “Notes” column suggesting lazy import.

Keep it simple; don’t refactor automatically yet.

Step 4: Optional Graph

Build import graph (module → dependencies) with ast parsing.

Optional for MVP but can be a .dot file for Graphviz.

Optional MVP+ Features (Post Weekend 2)

Compare PR vs main branch for import cost regression.

Local AI suggestions via Ollama/GPT4All (e.g., explain heavy import, suggest refactor).

Docker / Lambda profiling for real cold start measurement.

Deliverables for MVP

CLI: scan, top, json commands.

Reports: human-readable table + JSON output.

Per-module import time + memory measurement.

Minimal config + caching.

Good README:

Problem statement (why cold start matters).

Usage examples.

Screenshot of output.

Optional note: “future enhancements”.
