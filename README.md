# ColdPy

ColdPy profiles Python startup import cost by measuring import time and memory per module.
It is built for serverless, microservices, and large Python apps where cold start matters.

## What it measures

- Import duration (milliseconds)
- Import memory peak (MB) using `tracemalloc`
- Per-module status (success/error)
- Heavy module hints for lazy loading opportunities

## Safety caveat

ColdPy measures *real imports*, so target module import code is executed in isolated subprocesses.
This prevents state leakage between modules, but import side effects in target code may still occur.

## Install

```bash
uv sync
```

## Usage

```bash
coldpy scan
coldpy scan ./myproject
coldpy scan ./myproject --json report.json
coldpy top 10
coldpy top 20 --sort memory --threshold-mb 20
```

## Commands

- `coldpy scan [PATH=. ] [--json OUTPUT_JSON] [--threshold-ms N] [--threshold-mb N] [--no-cache]`
- `coldpy scan PATH [--python PYTHON] [--env-file ENV_FILE] [--no-project-env]`
- `coldpy top [N=10] [--sort time|memory] [--threshold-ms N] [--threshold-mb N]`

`coldpy top` reads `./.coldpy/cache.json` and fails if no cache exists.

For `scan`, ColdPy auto-detects project virtualenv Python in `.venv`, `venv`, or `env`
and auto-loads environment variables from `.env`/`.env.local` when present.
Use `--python` and `--env-file` only when you need to override auto-detection.

## JSON schema (v1)

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-02-20T10:00:00+00:00",
  "project_root": "/path/to/project",
  "settings": {
    "threshold_ms": 100,
    "threshold_mb": 50,
    "exclusions": ["tests", "venv"]
  },
  "summary": {
    "total_modules": 3,
    "scanned_modules": 2,
    "failed_modules": 1
  },
  "modules": [
    {
      "name": "pkg.fast",
      "file": "/path/to/project/pkg/fast.py",
      "import_time_ms": 1.234,
      "memory_mb": 0.123,
      "status": "ok",
      "error": null,
      "notes": []
    }
  ]
}
```

## Cache behavior

- Cache path: `./.coldpy/cache.json`
- Written by `scan` by default
- Disable with `--no-cache`
- Read by `top`

## Troubleshooting

- `Cache not found`: run `coldpy scan <path>` first.
- `No Python modules found`: verify path and exclusions.
- Import failures: check module side effects and importability from project root.

## PyPI release setup

GitHub workflows are included in `/Users/denis/Documents/ColdPy/.github/workflows`:

- `ci.yml`: test matrix on Python 3.10/3.11/3.12.
- `package.yml`: build and validate `sdist` + `wheel`.
- `publish.yml`: publish on GitHub Release (PyPI) or manual dispatch (TestPyPI/PyPI).

Recommended publishing model is Trusted Publisher (OIDC):

1. Create a PyPI project for `coldpy` (and optionally a TestPyPI project).
2. In PyPI project settings, add your GitHub repo as a trusted publisher.
3. Create a GitHub Release to publish to PyPI.
4. Use workflow dispatch with `target=testpypi` for preflight package checks.

If you prefer API tokens instead of OIDC, set `password` input in the publish action
and store the token in GitHub Secrets.
