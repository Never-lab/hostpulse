from __future__ import annotations

import app_paths


def test_not_frozen_in_pytest() -> None:
    assert app_paths.is_frozen() is False


def test_app_base_dir_is_repo_root() -> None:
    root = app_paths.get_app_base_dir()
    assert (root / "README.md").is_file()
    assert (root / "bin" / "engine.py").is_file()


def test_config_and_results_dirs_under_base() -> None:
    base = app_paths.get_app_base_dir()
    assert app_paths.get_config_dir() == base / "config"
    assert app_paths.get_results_dir() == base / "results"
    assert app_paths.get_bin_dir() == base / "bin"


def test_config_example_exists() -> None:
    example = app_paths.get_app_base_dir() / "config" / "config.example.json"
    assert example.is_file()
