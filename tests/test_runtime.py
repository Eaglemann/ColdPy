from pathlib import Path

from coldpy.runtime import build_scan_environment, load_project_env, resolve_python_executable


FIXTURE = Path(__file__).parent / "fixtures" / "sample_project"


def test_resolve_python_falls_back_to_current_interpreter() -> None:
    resolved = resolve_python_executable(FIXTURE)
    assert resolved.exists()


def test_load_project_env_from_default_file() -> None:
    env, source = load_project_env(FIXTURE)
    assert source is not None
    assert source.name == ".env"
    assert env["COLDPY_TEST_TOKEN"] == "present"
    assert env["EXTRA_VALUE"] == "hello"


def test_build_scan_environment_includes_extra_env() -> None:
    env = build_scan_environment({"COLDPY_X": "1"})
    assert env["COLDPY_X"] == "1"


def test_resolve_python_with_invalid_path_raises(tmp_path: Path) -> None:
    invalid = tmp_path / "missing-python"
    try:
        resolve_python_executable(FIXTURE, requested_python=invalid)
    except ValueError as exc:
        assert "Invalid python executable" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid python executable")


def test_resolve_python_keeps_symlink_path_for_venv_style_python(tmp_path: Path) -> None:
    real_python = tmp_path / "real-python"
    real_python.write_text("#!/bin/sh\n", encoding="utf-8")
    link_python = tmp_path / "venv-python"
    link_python.symlink_to(real_python)

    resolved = resolve_python_executable(FIXTURE, requested_python=link_python)
    assert resolved == link_python.absolute()
