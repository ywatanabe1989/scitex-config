"""Tests for scitex_config.local_state — per-package path resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from scitex_config import local_state


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request) -> Path:
    """Override $HOME and $SCITEX_DIR so tests don't touch the user's
    real ~/.scitex/ tree. Returns the fake $SCITEX_DIR root.

    Only chdir's to fake_home if `fake_repo` is NOT also being used by
    the test (so the two fixtures compose without trampling cwd)."""
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir(exist_ok=True)
    fake_scitex = tmp_path / "fake-scitex"
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("SCITEX_DIR", str(fake_scitex))
    if "fake_repo" not in request.fixturenames:
        monkeypatch.chdir(fake_home)
    return fake_scitex


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a tmp dir with a `.git/` marker so find_project_scope
    treats it as a repo root. cwd is set inside it."""
    repo = tmp_path / "myproj"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)
    return repo


def test_user_root_default_uses_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_home = tmp_path / "h"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("SCITEX_DIR", raising=False)
    assert local_state.user_root() == fake_home / ".scitex"


def test_user_root_honours_scitex_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom = tmp_path / "custom-scitex"
    monkeypatch.setenv("SCITEX_DIR", str(custom))
    assert local_state.user_root() == custom


def test_user_root_resolved_per_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Live env changes take effect mid-process."""
    monkeypatch.setenv("SCITEX_DIR", str(tmp_path / "first"))
    first = local_state.user_root()
    monkeypatch.setenv("SCITEX_DIR", str(tmp_path / "second"))
    second = local_state.user_root()
    assert first != second


def test_find_project_scope_returns_none_outside_repo(isolated_home: Path) -> None:
    assert local_state.find_project_scope("hpc") is None


def test_find_project_scope_returns_none_when_dir_missing(fake_repo: Path) -> None:
    """Repo exists but no `.scitex/<pkg>/` — returns None."""
    assert local_state.find_project_scope("hpc") is None


def test_find_project_scope_finds_existing_dir(fake_repo: Path) -> None:
    scope = fake_repo / ".scitex" / "hpc"
    scope.mkdir(parents=True)
    assert local_state.find_project_scope("hpc") == scope


def test_find_project_scope_walks_up(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """cwd deep inside the repo still finds the scope at repo root."""
    scope = fake_repo / ".scitex" / "hpc"
    scope.mkdir(parents=True)
    deep = fake_repo / "a" / "b" / "c"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    assert local_state.find_project_scope("hpc") == scope


def test_path_falls_back_to_user_when_no_repo(isolated_home: Path) -> None:
    """No repo around → resolve to $SCITEX_DIR/<pkg>/<sub>."""
    p = local_state.path("hpc", "config.yaml")
    assert p == isolated_home / "hpc" / "config.yaml"


def test_path_falls_back_when_project_scope_lacks_file(
    fake_repo: Path, isolated_home: Path
) -> None:
    """Project-scope dir exists but file inside doesn't — fall back to user scope."""
    (fake_repo / ".scitex" / "hpc").mkdir(parents=True)
    p = local_state.path("hpc", "config.yaml")
    assert p == isolated_home / "hpc" / "config.yaml"


def test_path_uses_project_scope_when_file_exists(
    fake_repo: Path, isolated_home: Path
) -> None:
    """File exists in project scope — that wins."""
    project = fake_repo / ".scitex" / "hpc"
    project.mkdir(parents=True)
    project_file = project / "config.yaml"
    project_file.write_text("project_scope: true\n")
    assert local_state.path("hpc", "config.yaml") == project_file


def test_user_path_skips_project_scope(fake_repo: Path, isolated_home: Path) -> None:
    """user_path always returns user-scope path even when project scope has the file."""
    project = fake_repo / ".scitex" / "hpc"
    project.mkdir(parents=True)
    (project / "host-id.yaml").write_text("project: yes\n")
    p = local_state.user_path("hpc", "host-id.yaml")
    assert p == isolated_home / "hpc" / "host-id.yaml"


def test_runtime_path_creates_seeds_in_user_scope(isolated_home: Path) -> None:
    """First call creates runtime/.gitkeep + README.md."""
    log = local_state.runtime_path("hpc", "dispatch.log")
    runtime_dir = isolated_home / "hpc" / "runtime"
    assert runtime_dir.is_dir()
    assert (runtime_dir / ".gitkeep").exists()
    assert (runtime_dir / "README.md").exists()
    assert log == runtime_dir / "dispatch.log"


def test_runtime_path_creates_seeds_in_project_scope(fake_repo: Path) -> None:
    """If project scope is active, seeds land there."""
    (fake_repo / ".scitex" / "hpc").mkdir(parents=True)
    log = local_state.runtime_path("hpc", "dispatch.log")
    runtime_dir = fake_repo / ".scitex" / "hpc" / "runtime"
    assert runtime_dir.is_dir()
    assert (runtime_dir / ".gitkeep").exists()
    assert (runtime_dir / "README.md").exists()
    assert log == runtime_dir / "dispatch.log"


def test_runtime_path_idempotent(isolated_home: Path) -> None:
    """Calling runtime_path twice doesn't clobber a customized README."""
    runtime_dir = isolated_home / "hpc" / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "README.md").write_text("custom content\n")
    local_state.runtime_path("hpc")
    assert (runtime_dir / "README.md").read_text() == "custom content\n"


def test_path_with_no_parts_returns_pkg_root(isolated_home: Path) -> None:
    assert local_state.path("hpc") == isolated_home / "hpc"


def test_user_path_with_no_parts_returns_pkg_root(isolated_home: Path) -> None:
    assert local_state.user_path("hpc") == isolated_home / "hpc"


def test_runtime_path_with_no_parts_returns_runtime_dir(isolated_home: Path) -> None:
    rt = local_state.runtime_path("hpc")
    assert rt == isolated_home / "hpc" / "runtime"
