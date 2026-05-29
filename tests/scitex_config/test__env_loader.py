#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-05-30 (ywatanabe)"
# File: ./tests/scitex_config/test__env_loader.py

"""Tests for the .src/.env env-loading functions in scitex_config."""

import os
from pathlib import Path
from typing import Iterator

import pytest

from scitex_config import load_env_from_path, load_scitex_env, parse_src_file


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


class TestParseSrcFile:
    """parse_src_file should parse bash-style assignments into a dict."""

    def test_parse_src_file_returns_expected_dict(self, tmp_path: Path) -> None:
        # Arrange
        src = tmp_path / "vars.src"
        src.write_text(
            '# comment\nexport FOO=bar\nBAZ="quoted value"\nEMPTY_LINE_BELOW=ok\n\n'
        )

        # Act
        result = parse_src_file(src)

        # Assert
        assert result == {
            "FOO": "bar",
            "BAZ": "quoted value",
            "EMPTY_LINE_BELOW": "ok",
        }

    def test_parse_src_file_expands_existing_env_var(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        os.environ["SCITEX_TEST_BASE"] = "/base"
        src = tmp_path / "vars.src"
        src.write_text("CHILD=${SCITEX_TEST_BASE}/child\n")

        # Act
        result = parse_src_file(src)

        # Assert
        assert result == {"CHILD": "/base/child"}


class TestLoadEnvFromPath:
    """load_env_from_path should read a single file or a directory of .src files."""

    def test_load_env_from_path_single_file_returns_dict(self, tmp_path: Path) -> None:
        # Arrange
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret\nDEBUG=1\n")

        # Act
        result = load_env_from_path(str(env_file))

        # Assert
        assert result == {"API_KEY": "secret", "DEBUG": "1"}

    def test_load_env_from_path_directory_merges_src_files(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "a.src").write_text("A=1\n")
        (tmp_path / "b.src").write_text("B=2\n")

        # Act
        result = load_env_from_path(str(tmp_path))

        # Assert
        assert result == {"A": "1", "B": "2"}

    def test_load_env_from_path_missing_path_returns_empty(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        missing = tmp_path / "does_not_exist.src"

        # Act
        result = load_env_from_path(str(missing))

        # Assert
        assert result == {}


class TestLoadScitexEnv:
    """load_scitex_env should apply $SCITEX_ENV_SRC contents to os.environ."""

    def test_load_scitex_env_returns_loaded_count(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        src = tmp_path / "app.src"
        src.write_text("SCITEX_TEST_X=1\nSCITEX_TEST_Y=2\n")
        os.environ["SCITEX_ENV_SRC"] = str(src)
        os.environ.pop("SCITEX_TEST_X", None)
        os.environ.pop("SCITEX_TEST_Y", None)

        # Act
        count = load_scitex_env()

        # Assert
        assert count == 2

    def test_load_scitex_env_applies_vars_to_environ(
        self, tmp_path: Path, env_var_guard: None
    ) -> None:
        # Arrange
        src = tmp_path / "app.src"
        src.write_text("SCITEX_TEST_X=1\n")
        os.environ["SCITEX_ENV_SRC"] = str(src)
        os.environ.pop("SCITEX_TEST_X", None)

        # Act
        load_scitex_env()

        # Assert
        assert os.environ["SCITEX_TEST_X"] == "1"

    def test_load_scitex_env_unset_returns_zero(self, env_var_guard: None) -> None:
        # Arrange
        os.environ.pop("SCITEX_ENV_SRC", None)

        # Act
        count = load_scitex_env()

        # Assert
        assert count == 0


# EOF
