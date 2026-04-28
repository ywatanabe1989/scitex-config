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
canonical-location: scitex-config/src/scitex_config/_skills/scitex-config/SKILL.md
tags: [scitex-config, scitex-package, config, paths, priority]
---

> **Interfaces:** Python ⭐⭐⭐ (primary) · CLI — · MCP — · Skills ⭐⭐ · Hook — · HTTP —

# scitex-config

Layered configuration + path management for the SciTeX ecosystem.
Two surfaces:

- **Public** (`scitex_config.*`) — convention-free primitives usable by
  any Python project.
- **Ecosystem-internal** (`scitex_config._ecosystem.*`) — helpers that
  embed SciTeX conventions; for `scitex-*` package authors only.

## Public API

### `PriorityConfig` — direct → yaml → env → default

```python
from scitex_config import PriorityConfig

pc = PriorityConfig(yaml_path="config/app.yaml")
db_url = pc.resolve(
    direct=cli_arg,            # 1. explicit caller-supplied
    key="database.url",        # 2. yaml lookup
    env_var="DATABASE_URL",    # 3. env var
    default="sqlite:///dev.db" # 4. last resort
)
```

The cascade is the **canonical pattern for every tunable in every
SciTeX package** — replaces ad-hoc `os.environ.get(...) or yaml.get(...)
or default` ladders that read inconsistently across the ecosystem.

### `ScitexConfig` + `get_config` — YAML-backed config object

```python
from scitex_config import get_config
config = get_config()              # loads ./config/*.yaml or $SCITEX_CONFIG
log_level = config.resolve("logging.level", default="INFO")
```

Same priority semantics as `PriorityConfig`, with a richer dict-like
surface for nested keys (`config.resolve("a.b.c")`).

### `ScitexPaths` + `get_paths` — `$SCITEX_DIR` path manager

```python
from scitex_config import get_paths
p = get_paths()
print(p.logs)   # $SCITEX_DIR/logs    (default ~/.scitex/logs)
print(p.cache)  # $SCITEX_DIR/cache
cache_dir = p.resolve("cache", user_supplied)  # priority cascade
```

`$SCITEX_DIR` defaults to `~/.scitex/` and is the ecosystem's single
relocator for all on-disk state.

### Utilities

- `load_dotenv()` — reads `.env` honoring the priority cascade
- `load_yaml(path)` — light wrapper that resolves env-var placeholders
- `get_scitex_dir()` — returns `Path($SCITEX_DIR)`

## Ecosystem-internal API (`_ecosystem`)

For `scitex-*` package authors. **Not stable**; may change without a
major bump.

```python
from scitex_config._ecosystem import local_state

# Resolves to <repo>/.scitex/<pkg-short>/<...> if running inside a repo
# whose .git/ ancestor contains that override; else $SCITEX_DIR/<pkg-short>/.
state_path = local_state.path("dataset", "datasets.db")

# Always under runtime/, with auto-seeded .gitkeep + README.md.
runtime = local_state.runtime_path("orochi", "shim-yamls")

# Forces user-scope (skips project-scope walk-up).
user_dir = local_state.user_path("core", "logs")
```

The walk-up resolution lets a developer override per-project state by
creating `<repo>/.scitex/<pkg-short>/`; production runs fall through to
`$SCITEX_DIR`. `pkg-short` strips the `scitex-` prefix
(`scitex-dataset` → `dataset`).

## When to use

- ✅ Any place a package reads a tunable (CLI flag, yaml key, env var,
  default)
- ✅ Any place a package writes runtime state (cache, logs, sessions)
- ✅ Any place a package needs the user's `$SCITEX_DIR`
- ❌ Per-call ephemeral options inside a single function — overkill

## Common mistakes

- **Importing `_ecosystem` from non-scitex code.** That surface is
  internal; use only `PriorityConfig` / `ScitexPaths` / `get_paths`.
- **Hardcoding `~/.cache/scitex-<pkg>/`.** This bypasses
  `$SCITEX_DIR` and the project-scope override. Always go through
  `local_state.path()` or `get_paths()`.
- **Reading `os.environ.get(...) or default` directly.** The agent
  loses the yaml + project-config layers; future operators can't override
  via the standard cascade.

## See also

- General skill `01_arch_06_local-state-directories.md` — canonical
  `<scitex_dir>/<pkg-short>/runtime/` layout policy.
- General skill `01_arch_04_environment-variables.md` — `SCITEX_*` env
  variable taxonomy.
- Failure playbook `98_quality_01_failure-playbook.md` §8–§9 — the
  `2026-04-28` migration class-action and the test fallout pattern.

<!-- EOF -->
