#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-09"
# File: ./tests/scitex/config/test__PriorityConfig.py

"""Tests for PriorityConfig class and load_dotenv, get_scitex_dir functions."""

import os
from pathlib import Path
from typing import Iterator

import pytest

from scitex_config import PriorityConfig, get_scitex_dir, load_dotenv


@pytest.fixture
def env_var_guard() -> Iterator[None]:
    """Snapshot os.environ and restore on teardown."""
    # Arrange
    original = dict(os.environ)
    try:
        yield
    finally:
        for key in list(os.environ):
            if key not in original:
                del os.environ[key]
        for key, value in original.items():
            os.environ[key] = value


# ----------------------------------------------------------------------------
# Basic init / repr
# ----------------------------------------------------------------------------


class TestPriorityConfigBasic:
    """Basic PriorityConfig functionality tests."""

    def test_default_initialization_returns_instance(self) -> None:
        # Arrange
        # Act
        config = PriorityConfig()
        # Assert
        assert config is not None

    def test_config_dict_init_get_returns_stored_value(self) -> None:
        # Arrange
        # Act
        config = PriorityConfig(config_dict={"port": 3000})
        # Assert
        assert config.get("port") == 3000

    def test_env_prefix_init_stores_prefix_on_instance(self) -> None:
        # Arrange
        # Act
        config = PriorityConfig(env_prefix="TEST_")
        # Assert
        assert config.env_prefix == "TEST_"

    def test_repr_contains_env_prefix(self) -> None:
        # Arrange
        config = PriorityConfig(config_dict={"a": 1, "b": 2}, env_prefix="APP_")
        # Act
        repr_str = repr(config)
        # Assert
        assert "APP_" in repr_str

    def test_repr_contains_config_dict_size(self) -> None:
        # Arrange
        config = PriorityConfig(config_dict={"a": 1, "b": 2}, env_prefix="APP_")
        # Act
        repr_str = repr(config)
        # Assert
        assert "2" in repr_str


# ----------------------------------------------------------------------------
# resolve() precedence
# ----------------------------------------------------------------------------


class TestPriorityConfigResolution:
    """Test priority resolution order: direct → config_dict → env → default."""

    def test_resolve_direct_value_beats_config_dict(self) -> None:
        # Arrange
        config = PriorityConfig(config_dict={"port": 3000}, env_prefix="TEST_")
        # Act
        result = config.resolve("port", direct_val=9000, default=8000)
        # Assert
        assert result == 9000

    def test_resolve_config_dict_beats_env_var(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_PORT"] = "5000"
        config = PriorityConfig(config_dict={"port": 3000}, env_prefix="TEST_")
        # Act
        result = config.resolve("port", default=8000)
        # Assert
        assert result == 3000

    def test_resolve_env_var_beats_default(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_HOST"] = "localhost"
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("host", default="0.0.0.0")
        # Assert
        assert result == "localhost"

    def test_resolve_falls_back_to_default(self) -> None:
        # Arrange
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("unknown_key", default="fallback")
        # Assert
        assert result == "fallback"


# ----------------------------------------------------------------------------
# Type conversion
# ----------------------------------------------------------------------------


class TestPriorityConfigTypeConversion:
    """Test type conversion in resolve()."""

    def test_int_type_returns_correct_int_value(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_COUNT"] = "42"
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("count", default=0, type=int)
        # Assert
        assert result == 42

    def test_int_type_returns_int_instance(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_COUNT"] = "42"
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("count", default=0, type=int)
        # Assert
        assert isinstance(result, int)

    def test_float_type_returns_correct_float_value(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_RATE"] = "3.14"
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("rate", default=0.0, type=float)
        # Assert
        assert result == 3.14

    @pytest.mark.parametrize("true_val", ["true", "1", "yes"])
    def test_bool_type_returns_true_for_truthy_string(
        self, env_var_guard: None, true_val: str
    ) -> None:
        # Arrange
        os.environ["TEST_DEBUG"] = true_val
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("debug", default=False, type=bool)
        # Assert
        assert result is True

    def test_list_type_splits_comma_separated_string(self, env_var_guard: None) -> None:
        # Arrange
        os.environ["TEST_ITEMS"] = "a,b,c"
        config = PriorityConfig(env_prefix="TEST_")
        # Act
        result = config.resolve("items", default=[], type=list)
        # Assert
        assert result == ["a", "b", "c"]


# ----------------------------------------------------------------------------
# Sensitive value masking
# ----------------------------------------------------------------------------


class TestPriorityConfigSensitiveValues:
    """Test sensitive value masking."""

    def test_sensitive_key_logged_value_is_masked(self) -> None:
        # Arrange
        config = PriorityConfig(config_dict={"api_key": "secret123"})
        # Act
        config.resolve("api_key", default="")
        log_entry = config.resolution_log[0]
        # Assert
        assert log_entry["value"] != "secret123"

    def test_mask_false_disables_sensitive_masking(self) -> None:
        # Arrange
        config = PriorityConfig(config_dict={"api_key": "secret123"})
        # Act
        config.resolve("api_key", default="", mask=False)
        log_entry = config.resolution_log[0]
        # Assert
        assert log_entry["value"] == "secret123"


# ----------------------------------------------------------------------------
# load_dotenv()
# ----------------------------------------------------------------------------


class TestLoadDotenv:
    """Test load_dotenv() function."""

    def test_load_dotenv_returns_true_for_explicit_path(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        path = tmp_path / ".env"
        path.write_text("TEST_DOTENV_VAR=explicit_value\n")
        os.environ.pop("TEST_DOTENV_VAR", None)
        # Act
        result = load_dotenv(str(path))
        # Assert
        assert result is True

    def test_load_dotenv_sets_env_var_from_explicit_path(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        path = tmp_path / ".env"
        path.write_text("TEST_DOTENV_VAR=explicit_value\n")
        os.environ.pop("TEST_DOTENV_VAR", None)
        # Act
        load_dotenv(str(path))
        # Assert
        assert os.environ.get("TEST_DOTENV_VAR") == "explicit_value"

    def test_load_dotenv_returns_false_for_nonexistent_path(self) -> None:
        # Arrange
        # Act
        result = load_dotenv("/nonexistent/path/.env")
        # Assert
        assert result is False

    def test_load_dotenv_skips_comment_lines_when_parsing(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        """Test load_dotenv skips comment lines."""
        # Arrange
        path = tmp_path / ".env"
        path.write_text("# Comment\nTEST_COMMENT_VAR=value\n")
        os.environ.pop("TEST_COMMENT_VAR", None)
        # Act
        load_dotenv(str(path))
        # Assert
        assert os.environ.get("TEST_COMMENT_VAR") == "value"

    def test_load_dotenv_strips_export_prefix(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        path = tmp_path / ".env"
        path.write_text("export TEST_EXPORT_VAR=exported_value\n")
        os.environ.pop("TEST_EXPORT_VAR", None)
        # Act
        load_dotenv(str(path))
        # Assert
        assert os.environ.get("TEST_EXPORT_VAR") == "exported_value"

    def test_load_dotenv_strips_surrounding_double_quotes(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        path = tmp_path / ".env"
        path.write_text('TEST_QUOTE_VAR="quoted value"\n')
        os.environ.pop("TEST_QUOTE_VAR", None)
        # Act
        load_dotenv(str(path))
        # Assert
        assert os.environ.get("TEST_QUOTE_VAR") == "quoted value"

    def test_load_dotenv_preserves_existing_env_var(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        """Test load_dotenv does not override existing env vars."""
        # Arrange
        path = tmp_path / ".env"
        path.write_text("TEST_EXISTING_VAR=from_dotenv\n")
        os.environ["TEST_EXISTING_VAR"] = "from_shell"
        # Act
        load_dotenv(str(path))
        # Assert
        assert os.environ.get("TEST_EXISTING_VAR") == "from_shell"


# ----------------------------------------------------------------------------
# load_dotenv(walk_up=True) — parent-directory walking
# ----------------------------------------------------------------------------


@pytest.fixture
def cwd_guard() -> Iterator[None]:
    """Snapshot cwd and restore on teardown."""
    original = Path.cwd()
    try:
        yield
    finally:
        os.chdir(original)


@pytest.fixture
def nested_env_tree(tmp_path: Path) -> Path:
    """Fixture: tmp_path/.env, tmp_path/mid/.env, tmp_path/mid/leaf/.env.

    Each .env defines one distinct WALKUP_*_VAR. Returns the deepest dir.
    """
    root = tmp_path
    mid = root / "mid"
    leaf = mid / "leaf"
    mid.mkdir()
    leaf.mkdir()
    (root / ".env").write_text("WALKUP_ROOT_VAR=root_value\n")
    (mid / ".env").write_text("WALKUP_MID_VAR=mid_value\n")
    (leaf / ".env").write_text("WALKUP_LEAF_VAR=leaf_value\n")
    for k in ("WALKUP_ROOT_VAR", "WALKUP_MID_VAR", "WALKUP_LEAF_VAR"):
        os.environ.pop(k, None)
    return leaf


@pytest.fixture
def shared_key_tree(tmp_path: Path) -> Path:
    """Fixture: root/.env and root/leaf/.env both define WALKUP_SHARED_VAR."""
    root = tmp_path
    leaf = root / "leaf"
    leaf.mkdir()
    (root / ".env").write_text("WALKUP_SHARED_VAR=from_root\n")
    (leaf / ".env").write_text("WALKUP_SHARED_VAR=from_leaf\n")
    os.environ.pop("WALKUP_SHARED_VAR", None)
    return leaf


@pytest.fixture
def stop_at_tree(tmp_path: Path) -> Path:
    """Fixture: outer/inner/leaf, each with own .env. Returns leaf."""
    outer = tmp_path / "outer"
    inner = outer / "inner"
    leaf = inner / "leaf"
    outer.mkdir()
    inner.mkdir()
    leaf.mkdir()
    (outer / ".env").write_text("WALKUP_OUTER_VAR=should_not_load\n")
    (inner / ".env").write_text("WALKUP_INNER_VAR=inner_value\n")
    (leaf / ".env").write_text("WALKUP_LEAF_VAR=leaf_value\n")
    for k in (
        "WALKUP_OUTER_VAR",
        "WALKUP_INNER_VAR",
        "WALKUP_LEAF_VAR",
    ):
        os.environ.pop(k, None)
    return leaf


@pytest.fixture
def fake_home_tree(tmp_path: Path) -> Path:
    """Fixture: above/fake_home/project, each with own .env.

    Sets HOME=fake_home for the test (restored by env_var_guard).
    Returns the project dir.
    """
    above = tmp_path / "above"
    fake_home = above / "fake_home"
    project = fake_home / "project"
    above.mkdir()
    fake_home.mkdir()
    project.mkdir()
    (above / ".env").write_text("WALKUP_ABOVE_HOME_VAR=should_not_load\n")
    (fake_home / ".env").write_text("WALKUP_HOME_VAR=home_value\n")
    (project / ".env").write_text("WALKUP_PROJECT_VAR=project_value\n")
    for k in (
        "WALKUP_ABOVE_HOME_VAR",
        "WALKUP_HOME_VAR",
        "WALKUP_PROJECT_VAR",
    ):
        os.environ.pop(k, None)
    os.environ["HOME"] = str(fake_home)
    return project


class TestLoadDotenvWalkUp:
    """Test load_dotenv(walk_up=True) parent-directory walking."""

    def test_walk_up_returns_true_when_any_env_found(
        self,
        nested_env_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(nested_env_tree)
        # Act
        result = load_dotenv(walk_up=True, stop_at=nested_env_tree.parent.parent)
        # Assert
        assert result is True

    def test_walk_up_loads_root_env_var(
        self,
        nested_env_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(nested_env_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=nested_env_tree.parent.parent)
        # Assert
        assert os.environ.get("WALKUP_ROOT_VAR") == "root_value"

    def test_walk_up_loads_mid_env_var(
        self,
        nested_env_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(nested_env_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=nested_env_tree.parent.parent)
        # Assert
        assert os.environ.get("WALKUP_MID_VAR") == "mid_value"

    def test_walk_up_loads_leaf_env_var(
        self,
        nested_env_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(nested_env_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=nested_env_tree.parent.parent)
        # Assert
        assert os.environ.get("WALKUP_LEAF_VAR") == "leaf_value"

    def test_walk_up_closer_env_wins_over_distant(
        self,
        shared_key_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(shared_key_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=shared_key_tree.parent)
        # Assert
        assert os.environ.get("WALKUP_SHARED_VAR") == "from_leaf"

    def test_walk_up_loads_leaf_when_stop_at_inner(
        self,
        stop_at_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        inner = stop_at_tree.parent
        os.chdir(stop_at_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=inner)
        # Assert
        assert os.environ.get("WALKUP_LEAF_VAR") == "leaf_value"

    def test_walk_up_loads_inner_when_stop_at_inner(
        self,
        stop_at_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        inner = stop_at_tree.parent
        os.chdir(stop_at_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=inner)
        # Assert
        assert os.environ.get("WALKUP_INNER_VAR") == "inner_value"

    def test_walk_up_skips_outer_when_stop_at_inner(
        self,
        stop_at_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        inner = stop_at_tree.parent
        os.chdir(stop_at_tree)
        # Act
        load_dotenv(walk_up=True, stop_at=inner)
        # Assert
        assert os.environ.get("WALKUP_OUTER_VAR") is None

    def test_walk_up_loads_project_env_when_home_stop(
        self,
        fake_home_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(fake_home_tree)
        # Act
        load_dotenv(walk_up=True)
        # Assert
        assert os.environ.get("WALKUP_PROJECT_VAR") == "project_value"

    def test_walk_up_loads_home_env_when_home_stop(
        self,
        fake_home_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(fake_home_tree)
        # Act
        load_dotenv(walk_up=True)
        # Assert
        assert os.environ.get("WALKUP_HOME_VAR") == "home_value"

    def test_walk_up_skips_above_home_env(
        self,
        fake_home_tree: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        os.chdir(fake_home_tree)
        # Act
        load_dotenv(walk_up=True)
        # Assert
        assert os.environ.get("WALKUP_ABOVE_HOME_VAR") is None

    def test_walk_up_false_does_not_load_parent_env(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        """walk_up=False (default) must keep legacy cwd-only-then-home semantics."""
        # Arrange: parent has .env, leaf does not. Legacy behavior must skip
        # the parent and only consider cwd + $HOME.
        parent = tmp_path / "parent"
        leaf = parent / "leaf"
        parent.mkdir()
        leaf.mkdir()
        (parent / ".env").write_text("WALKUP_PARENT_ONLY_VAR=parent_value\n")
        os.environ.pop("WALKUP_PARENT_ONLY_VAR", None)
        os.chdir(leaf)
        # Act
        load_dotenv(walk_up=False)
        # Assert: parent's .env must NOT be loaded under legacy behavior.
        assert os.environ.get("WALKUP_PARENT_ONLY_VAR") is None

    def test_walk_up_process_env_overrides_dotenv(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        """Process env wins over any loaded .env (closer or distant)."""
        # Arrange
        root = tmp_path
        leaf = root / "leaf"
        leaf.mkdir()
        (root / ".env").write_text("WALKUP_PROC_VAR=from_root\n")
        (leaf / ".env").write_text("WALKUP_PROC_VAR=from_leaf\n")
        os.environ["WALKUP_PROC_VAR"] = "from_process"
        os.chdir(leaf)
        # Act
        load_dotenv(walk_up=True, stop_at=root)
        # Assert
        assert os.environ.get("WALKUP_PROC_VAR") == "from_process"

    def test_walk_up_no_env_files_returns_false(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange: nested dirs, no .env anywhere.
        leaf = tmp_path / "a" / "b" / "c"
        leaf.mkdir(parents=True)
        os.chdir(leaf)
        # Act
        result = load_dotenv(walk_up=True, stop_at=tmp_path)
        # Assert
        assert result is False

    def test_explicit_path_loads_when_walk_up_set(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        # Arrange
        explicit = tmp_path / "custom.env"
        explicit.write_text("WALKUP_EXPLICIT_VAR=explicit\n")
        os.environ.pop("WALKUP_EXPLICIT_VAR", None)
        os.chdir(tmp_path)
        # Act
        load_dotenv(str(explicit), walk_up=True, stop_at=tmp_path)
        # Assert
        assert os.environ.get("WALKUP_EXPLICIT_VAR") == "explicit"

    def test_explicit_path_skips_nearby_env_files(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        """Explicit dotenv_path must short-circuit walk_up — no walking."""
        # Arrange
        root = tmp_path
        leaf = root / "leaf"
        leaf.mkdir()
        explicit = root / "custom.env"
        explicit.write_text("WALKUP_EXPLICIT_VAR=explicit\n")
        (root / ".env").write_text("WALKUP_PARENT_VAR=parent\n")
        for k in ("WALKUP_EXPLICIT_VAR", "WALKUP_PARENT_VAR"):
            os.environ.pop(k, None)
        os.chdir(leaf)
        # Act
        load_dotenv(str(explicit), walk_up=True, stop_at=root)
        # Assert
        assert os.environ.get("WALKUP_PARENT_VAR") is None

    def test_walk_up_stop_at_accepts_string_path(
        self,
        tmp_path: Path,
        env_var_guard: None,
        cwd_guard: None,
    ) -> None:
        """stop_at should accept a str path, not just Path."""
        # Arrange
        root = tmp_path
        leaf = root / "leaf"
        leaf.mkdir()
        (root / ".env").write_text("WALKUP_STR_STOP_VAR=root_value\n")
        os.environ.pop("WALKUP_STR_STOP_VAR", None)
        os.chdir(leaf)
        # Act
        load_dotenv(walk_up=True, stop_at=str(root))
        # Assert
        assert os.environ.get("WALKUP_STR_STOP_VAR") == "root_value"


# ----------------------------------------------------------------------------
# get_scitex_dir()
# ----------------------------------------------------------------------------


class TestGetScitexDir:
    """Test get_scitex_dir() function."""

    def test_default_value_is_home_dot_scitex(self, env_var_guard: None) -> None:
        # Arrange
        os.environ.pop("SCITEX_DIR", None)
        # Act
        result = get_scitex_dir()
        # Assert
        assert result == Path.home() / ".scitex"

    def test_env_var_overrides_default_path(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        os.environ["SCITEX_DIR"] = str(tmp_path)
        # Act
        result = get_scitex_dir()
        # Assert
        assert result == tmp_path

    def test_direct_val_overrides_env_var(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        env_dir = tmp_path / "env"
        direct_dir = tmp_path / "direct"
        env_dir.mkdir()
        direct_dir.mkdir()
        os.environ["SCITEX_DIR"] = str(env_dir)
        # Act
        result = get_scitex_dir(direct_val=str(direct_dir))
        # Assert
        assert result == direct_dir

    def test_direct_val_with_tilde_expands_to_home(self) -> None:
        # Arrange
        # Act
        result = get_scitex_dir(direct_val="~/custom_scitex")
        # Assert
        assert "~" not in str(result)


if __name__ == "__main__":
    import pytest as _pytest

    _pytest.main([os.path.abspath(__file__)])
