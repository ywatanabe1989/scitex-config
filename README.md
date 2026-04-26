# scitex-config

Configuration helpers (YAML + dotenv with layered priority) extracted from the [SciTeX](https://github.com/ywatanabe1989/scitex-python) ecosystem as a standalone package.

## Install

```bash
pip install scitex-config
```

## API

```python
import scitex_config as cfg

# YAML-based (recommended)
config = cfg.get_config()
print(config.MY_KEY)

# Path resolution
paths = cfg.get_paths()
paths.function_cache  # ~/.scitex/cache/function/...

# Layered (env > .env > yaml > defaults)
pc = cfg.PriorityConfig()
pc["DATABASE_URL"]
```

## Status

Standalone fork of `scitex.config`. Only dep is `PyYAML`. The umbrella
package's `scitex.config` import path is preserved via a `sys.modules`-alias
bridge.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).
