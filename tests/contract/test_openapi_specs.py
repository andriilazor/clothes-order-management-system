from pathlib import Path

import pytest
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

OPENAPI_DIR = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi"
SPECS = sorted(OPENAPI_DIR.glob("*.yaml"))
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}
VERSIONED_PREFIXES = ("/api/v1/", "/internal/v1/")


def test_openapi_specs_exist() -> None:
    assert SPECS, f"no OpenAPI files in {OPENAPI_DIR}"


@pytest.mark.req("NFR-12")
@pytest.mark.parametrize("spec_path", SPECS, ids=lambda path: path.name)
def test_spec_is_valid_openapi_31(spec_path: Path) -> None:
    spec, _ = read_from_filename(str(spec_path))

    assert str(spec["openapi"]).startswith("3.1")
    validate(spec)


@pytest.mark.req("NFR-12")
@pytest.mark.parametrize("spec_path", SPECS, ids=lambda path: path.name)
def test_paths_are_versioned(spec_path: Path) -> None:
    spec, _ = read_from_filename(str(spec_path))

    unversioned = [path for path in spec["paths"] if not path.startswith(VERSIONED_PREFIXES)]

    assert unversioned == []


@pytest.mark.req("NFR-12")
@pytest.mark.parametrize("spec_path", SPECS, ids=lambda path: path.name)
def test_every_operation_has_an_id_and_a_response_example(spec_path: Path) -> None:
    spec, _ = read_from_filename(str(spec_path))
    problems: list[str] = []

    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method not in HTTP_METHODS:
                continue
            if "operationId" not in operation:
                problems.append(f"{method.upper()} {path}: no operationId")
            has_example = any(
                "examples" in media
                for response in operation["responses"].values()
                for media in response.get("content", {}).values()
            )
            if not has_example:
                problems.append(f"{method.upper()} {path}: no response example")

    assert problems == []
