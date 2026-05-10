# scitex-config

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>Configuration + path management with `direct → yaml → env → default` priority cascade.</b></p>

<p align="center">
  <a href="https://scitex-config.readthedocs.io/">Full Documentation</a> · <code>uv pip install scitex-config[all]</code>
</p>

<!-- scitex-badges:start -->
<p align="center">
  <a href="https://pypi.org/project/scitex-config/"><img src="https://img.shields.io/pypi/v/scitex-config.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/scitex-config/"><img src="https://img.shields.io/pypi/pyversions/scitex-config.svg" alt="Python"></a>
  <a href="https://github.com/ywatanabe1989/scitex-config/actions/workflows/test.yml"><img src="https://github.com/ywatanabe1989/scitex-config/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/ywatanabe1989/scitex-config/actions/workflows/install-test.yml"><img src="https://github.com/ywatanabe1989/scitex-config/actions/workflows/install-test.yml/badge.svg" alt="Install Test"></a>
  <a href="https://codecov.io/gh/ywatanabe1989/scitex-config"><img src="https://codecov.io/gh/ywatanabe1989/scitex-config/graph/badge.svg" alt="Coverage"></a>
  <a href="https://scitex-config.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/scitex-config/badge/?version=latest" alt="Docs"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/license-AGPL_v3-blue.svg" alt="License: AGPL v3"></a>
</p>
<!-- scitex-badges:end -->

---

## Installation

```bash
pip install scitex-config
```

## Architecture

```
scitex-config/
├── src/scitex_config/
│   ├── __init__.py              # get_config, get_paths, PriorityConfig
│   ├── _config.py               # YAML loader + dotted-path resolve()
│   ├── _paths.py                # ~/.scitex/cache, function_cache, ...
│   ├── _priority.py             # PriorityConfig: direct > yaml > env > default
│   └── _bridge.py               # sys.modules alias -> scitex.config
└── tests/
```

## Quick Start

```python
import scitex_config as cfg

config = cfg.get_config()
log_level = config.resolve("logging.level", default="INFO")

paths = cfg.get_paths()
print(paths.cache)            # ~/.scitex/cache
```

## 1 Interfaces

<details open>
<summary><strong>Python API</strong></summary>

<br>

```python
import scitex_config as cfg

# YAML-based (recommended)
config = cfg.get_config()
print(config.MY_KEY)
log_level = config.resolve("logging.level", default="INFO")

# Path resolution
paths = cfg.get_paths()
paths.function_cache       # ~/.scitex/cache/function/...

# Layered priority cascade (direct > yaml > env > default)
pc = cfg.PriorityConfig(yaml_path="config/app.yaml")
db_url = pc.resolve(
    direct=cli_arg,
    key="database.url",
    env_var="DATABASE_URL",
    default="sqlite:///dev.db",
)
```

</details>

## Demo

```mermaid
flowchart LR
    D[direct=cli_arg] -->|wins if not None| R[PriorityConfig.resolve]
    Y["yaml: config/app.yaml<br/>database.url"] -->|2nd| R
    E["env: DATABASE_URL"] -->|3rd| R
    F["default='sqlite:///dev.db'"] -->|fallback| R
    R --> V["resolved value"]
```

## Status

Standalone fork of `scitex.config`. Only dep is `PyYAML`. The umbrella
package's `scitex.config` import path is preserved via a `sys.modules`-alias
bridge.

## Part of SciTeX

`scitex-config` is part of [**SciTeX**](https://scitex.ai). Install via
the umbrella with `pip install scitex[config]` to use as
`scitex.config` (Python) or `scitex config ...` (CLI).

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>
