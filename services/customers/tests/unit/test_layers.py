import importlib

import pytest

LAYERS = ("domain", "application", "adapters.inbound", "adapters.outbound", "bootstrap")


@pytest.mark.req("NFR-13", "NFR-14")
@pytest.mark.parametrize("layer", LAYERS)
def test_hexagonal_layer_package_exists(layer: str) -> None:
    importlib.import_module(f"customers.{layer}")
