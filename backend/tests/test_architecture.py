'''
Architecture rules (the dependency rule of clean architecture): source code dependencies only point inward.

    domain  <-  application  <-  infrastructure / interface  <-  Container (composition root)

- domain imports nothing from the other layers and no frameworks or drivers.
- application imports only the domain (and the shared CommonErrors), never an implementation or a framework.
- infrastructure and interface do not import each other.
'''
import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
CONTEXTS = ("UserLogin", "WI29_Server")
LAYERS = ("domain", "application", "infrastructure", "interface")
OUTER = {"infrastructure", "interface"}
THIRD_PARTY = {"fastapi", "starlette", "pydantic", "uvicorn", "psycopg", "pymongo", "gridfs", "bson", "requests",
               "flask", "sqlalchemy"}


def importsOf(path: Path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module


def modules(layer: str):
    for context in CONTEXTS:
        for path in sorted((BACKEND / context / layer).glob("*.py")):
            yield context, path


def layerOf(module: str):
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] in CONTEXTS and parts[1] in LAYERS:
        return parts[1]
    return None


@pytest.mark.parametrize("layer,forbidden", [
    ("domain", {"application", "infrastructure", "interface"}),
    ("application", OUTER),
])
def test_inner_layers_do_not_import_outer_layers(layer, forbidden):
    for _, path in modules(layer):
        for module in importsOf(path):
            assert layerOf(module) not in forbidden, f"{path.name} ({layer}) imports {module}"


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_use_no_frameworks_or_drivers(layer):
    for _, path in modules(layer):
        for module in importsOf(path):
            assert module.split(".")[0] not in THIRD_PARTY, f"{path.name} ({layer}) imports {module}"


def test_infrastructure_and_interface_do_not_import_each_other():
    for layer, other in (("infrastructure", "interface"), ("interface", "infrastructure")):
        for _, path in modules(layer):
            for module in importsOf(path):
                assert layerOf(module) != other, f"{path.name} ({layer}) imports {module}"


def test_user_login_does_not_depend_on_the_web_server():
    for layer in LAYERS:
        for path in sorted((BACKEND / "UserLogin" / layer).glob("*.py")):
            for module in importsOf(path):
                assert module.split(".")[0] != "WI29_Server", f"{path.name} imports {module}"


# Another bounded context is reached through a port (e.g. Accounts), never by importing its classes.
@pytest.mark.parametrize("layer", ["domain", "application", "interface"])
def test_web_server_core_does_not_import_the_user_login_context(layer):
    for path in sorted((BACKEND / "WI29_Server" / layer).glob("*.py")):
        for module in importsOf(path):
            assert module.split(".")[0] != "UserLogin", f"{path.name} ({layer}) imports {module}"


IO_MODULES = {"os", "sys", "socket", "subprocess", "pathlib", "time", "threading", "shutil", "sqlite3", "http", "urllib"}


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_do_no_io(layer):
    for _, path in modules(layer):
        for module in importsOf(path):
            assert module.split(".")[0] not in IO_MODULES, f"{path.name} ({layer}) imports {module}"


def test_only_the_composition_root_builds_infrastructure():
    server = BACKEND / "WI29_Server"
    for path in sorted(server.rglob("*.py")):
        relative = path.relative_to(server)
        if relative.parts[0] == "infrastructure" or relative.name == "Container.py":
            continue
        for module in importsOf(path):
            assert layerOf(module) != "infrastructure", f"{relative} imports {module}"
