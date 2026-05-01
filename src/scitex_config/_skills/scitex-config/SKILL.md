---
name: scitex-config
description: Configuration primitives for the SciTeX ecosystem — `PriorityConfig` (direct → yaml → env → default cascade for resolving any tunable), `ScitexConfig`+`get_config()` (YAML-based config object with the same cascade semantics), `ScitexPaths`+`get_paths()` (centralized `$SCITEX_DIR/<subdir>` path manager), and the ecosystem-internal `scitex_config._ecosystem.local_state` (project-scope-aware path resolver that walks up to `.git/` and falls back to `$SCITEX_DIR/<pkg-short>/`). Drop-in replacement for ad-hoc `os.environ.get(...) or yaml.safe_load(...) or default` ladders, scattered `Path.home()/'.cache'/'pkg'` hardcodes, and per-package `_paths.py` modules. Use whenever a SciTeX package needs to read a tunable, resolve a runtime/cache directory, or honor project-level overrides.
primary_interface: python
interfaces:
  python: 3
  cli: 0
  mcp: 0
  skills: 2
  hook: 0
  http: 0
tags: [scitex-config, scitex-package, config, paths, priority]
---

> **Interfaces:** Python ⭐⭐⭐ (primary) · Skills ⭐⭐

# scitex-config

Layered configuration + path management for the SciTeX ecosystem.

- **Public** (`scitex_config.*`) — convention-free primitives usable by any project.
- **Ecosystem-internal** (`scitex_config._ecosystem.*`) — embeds SciTeX conventions; for scitex-* package authors only.

## Public API

```python
from scitex_config import PriorityConfig, get_config, get_paths

# direct → yaml → env → default cascade
pc = PriorityConfig(yaml_path="config/app.yaml")
db = pc.resolve(direct=cli_arg, key="database.url",
                env_var="DATABASE_URL", default="sqlite:///dev.db")

# Same cascade for nested keys via the config object.
config = get_config()
log_level = config.resolve("logging.level", default="INFO")

# `$SCITEX_DIR` path manager.
p = get_paths()
print(p.logs, p.cache)                     # ~/.scitex/logs, ~/.scitex/cache
cache_dir = p.resolve("cache", user_supplied)
```

Utilities: `load_dotenv()`, `load_yaml(path)`, `get_scitex_dir()`.

## Ecosystem-internal API (`_ecosystem`)

```python
from scitex_config._ecosystem import local_state

# Project-scope-aware: walks up to .git/, falls back to $SCITEX_DIR/<pkg-short>/.
state_path = local_state.path("dataset", "datasets.db")
runtime = local_state.runtime_path("orochi", "shim-yamls")
user_dir = local_state.user_path("core", "logs")
```

`pkg-short` strips the `scitex-` prefix (`scitex-dataset` → `dataset`).
**Not stable** — may change without a major bump; for scitex-* authors only.

## When to use

- ✅ Reading any tunable (CLI flag, yaml, env, default) — use the cascade
- ✅ Writing runtime state (cache / logs / sessions)
- ✅ Resolving the user's `$SCITEX_DIR`
- ❌ Per-call ephemeral options — overkill

## Pitfalls

- **Importing `_ecosystem` from non-scitex code** — internal surface.
- **Hardcoding `~/.cache/scitex-<pkg>/`** — bypasses `$SCITEX_DIR` and
  project-scope override. Use `local_state.path()` or `get_paths()`.
- **`os.environ.get(...) or default`** — loses yaml + project-config layers.

## See also

- General `01_arch_06_local-state-directories.md` — runtime path policy
- General `01_arch_04_environment-variables.md` — `SCITEX_*` taxonomy
- Failure playbook `98_quality_01_failure-playbook.md` §8–§9
