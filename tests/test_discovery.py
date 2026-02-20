from pathlib import Path

from coldpy.discovery import discover_modules


FIXTURE = Path(__file__).parent / "fixtures" / "sample_project"


def test_discovery_excludes_tests_and_maps_modules() -> None:
    modules = discover_modules(FIXTURE)
    names = [m.name for m in modules]

    assert "pkg.__init__" not in names
    assert "tests.test_should_ignore" not in names
    assert "pkg" in names
    assert "pkg.fast" in names
    assert "pkg.slowish" in names
    assert "pkg.broken" in names


def test_discovery_invalid_path_raises() -> None:
    invalid = FIXTURE / "does_not_exist"
    try:
        discover_modules(invalid)
    except ValueError as exc:
        assert "Invalid scan path" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid path")
