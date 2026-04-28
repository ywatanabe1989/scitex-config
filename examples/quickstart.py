"""Quickstart for scitex_config.

Loads a YAML config from disk, inspects ScitexPaths, and shows the
ENV_REGISTRY of known SciTeX environment variables.
"""

import tempfile
from pathlib import Path
from textwrap import dedent

import scitex_config as sc


def main() -> int:
    # Persistent SciTeX paths (~/.scitex/* by default)
    paths = sc.get_paths()
    print(f"scitex base: {paths.base}")
    print(f"cache dir:   {paths.cache}")
    print(f"logs dir:    {paths.logs}")
    print(f"scitex_dir() helper: {sc.get_scitex_dir()}")

    # Round-trip a YAML config through `load_yaml`
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "exp.yaml"
        cfg.write_text(
            dedent(
                """
                experiment:
                  name: quickstart
                  seed: 42
                  lr: 0.001
                tags: [demo, batch_a]
                """
            ).strip()
        )
        loaded = sc.load_yaml(str(cfg))
        print(f"\nLoaded YAML: {loaded}")
        assert loaded["experiment"]["seed"] == 42

    # Ecosystem-internal helpers (scitex package authors only — not a
    # stable public API; see scitex_config._ecosystem.__doc__).
    from scitex_config._ecosystem import env_registry as er

    print("\nKnown SciTeX env-var modules:", er.get_all_modules()[:6])
    for ev in list(er.ENV_REGISTRY)[:3]:
        name = getattr(ev, "name", str(ev))
        default = getattr(ev, "default", None)
        print(f"  {name:<25} default={default!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
